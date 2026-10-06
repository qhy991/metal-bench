import Foundation
import Metal
import Darwin

struct Job: Decodable {
    let rows: Int, columns: Int
    let x: [Float], weight: [Float], epsilon: Float
    let source: String, entry: String, threads: Int, parameters: Bool
    let expected_device: String, timing: Bool
}
enum Failure: Error { case message(String) }
func require(_ valid: Bool, _ message: String) throws {
    if !valid { throw Failure.message(message) }
}

func main() throws {
    try require(CommandLine.arguments.count == 2, "one job path required")
    let job = try JSONDecoder().decode(Job.self, from: Data(contentsOf: URL(fileURLWithPath: CommandLine.arguments[1])))
    try require(job.rows > 0 && job.columns > 0 && job.rows <= 4096 && job.columns <= 65536, "bounded positive shape required")
    try require(job.rows * job.columns <= 4_194_304 && job.x.count == job.rows*job.columns && job.weight.count == job.columns, "input extent differs")
    try require(job.epsilon > 0 && job.epsilon.isFinite && job.x.allSatisfy({$0.isFinite}) && job.weight.allSatisfy({$0.isFinite}), "finite input required")
    // Cooperate with the existing M4 per-user allocation lock. No new lock namespace.
    // This excludes cooperating user jobs, not other users or GUI GPU activity.
    let lock = URL(fileURLWithPath: NSTemporaryDirectory()).appendingPathComponent("open-cake-ir-metal-\(geteuid()).lock").path
    let fd = open(lock, O_CREAT | O_RDWR | O_NOFOLLOW, S_IRUSR | S_IWUSR)
    try require(fd >= 0, "allocation lock could not be opened")
    defer { close(fd) }
    var info = stat()
    try require(fstat(fd, &info) == 0 && info.st_uid == geteuid() && info.st_nlink == 1 && (info.st_mode & S_IFMT) == S_IFREG, "allocation lock ownership/type differs")
    try require(flock(fd, LOCK_EX | LOCK_NB) == 0, "device busy; no retry")
    defer { flock(fd, LOCK_UN) }
    guard let device = MTLCreateSystemDefaultDevice(), let queue = device.makeCommandQueue() else { throw Failure.message("Metal unavailable") }
    try require(device.name == job.expected_device && device.supportsFamily(.apple9), "exact Apple M4 target required")
    let options = MTLCompileOptions(); options.fastMathEnabled = false
    let library = try device.makeLibrary(source: String(contentsOfFile: job.source, encoding: .utf8), options: options)
    guard let function = library.makeFunction(name: job.entry) else { throw Failure.message("entry point missing") }
    let pipeline = try device.makeComputePipelineState(function: function)
    try require(pipeline.threadExecutionWidth == 32 && job.threads > 0 && job.threads <= pipeline.maxTotalThreadsPerThreadgroup, "threadgroup unsupported")
    let input = job.x.withUnsafeBytes { device.makeBuffer(bytes: $0.baseAddress!, length: $0.count, options: .storageModeShared) }!
    let weights = job.weight.withUnsafeBytes { device.makeBuffer(bytes: $0.baseAddress!, length: $0.count, options: .storageModeShared) }!
    let out = device.makeBuffer(length: job.x.count*4, options: .storageModeShared)!
    func unchanged() -> Bool {
        job.x.withUnsafeBytes { memcmp(input.contents(), $0.baseAddress!, $0.count) == 0 } &&
        job.weight.withUnsafeBytes { memcmp(weights.contents(), $0.baseAddress!, $0.count) == 0 }
    }
    func dispatch(_ repetitions: Int) throws -> Double {
        guard let command = queue.makeCommandBuffer(), let encoder = command.makeComputeCommandEncoder() else { throw Failure.message("command allocation failed") }
        encoder.setComputePipelineState(pipeline)
        encoder.setBuffer(input, offset: 0, index: 0); encoder.setBuffer(weights, offset: 0, index: 1); encoder.setBuffer(out, offset: 0, index: 2)
        if job.parameters {
            var columns = UInt32(job.columns), epsilon = job.epsilon
            encoder.setBytes(&columns, length: 4, index: 3); encoder.setBytes(&epsilon, length: 4, index: 4)
        }
        for _ in 0..<repetitions {
            encoder.dispatchThreadgroups(MTLSize(width: job.rows, height: 1, depth: 1), threadsPerThreadgroup: MTLSize(width: job.threads, height: 1, depth: 1))
        }
        encoder.endEncoding(); command.commit(); command.waitUntilCompleted()
        try require(command.status == .completed, "GPU command failed: \(String(describing: command.error))")
        try require(unchanged(), "candidate mutated inputs")
        return (command.gpuEndTime-command.gpuStartTime)*1000
    }
    // Sentinel prevents unwritten outputs from passing as allocator contents.
    let pointer = out.contents().bindMemory(to: Float.self, capacity: job.x.count)
    for i in 0..<job.x.count { pointer[i] = Float.nan }
    _ = try dispatch(1)
    let referenceOutput = Data(bytes: out.contents(), count: job.x.count*4)
    let values = Array(UnsafeBufferPointer(start: pointer, count: job.x.count))
    try require(values.allSatisfy({$0.isFinite}), "nonfinite or unwritten output")
    var intervals: [Double] = []
    if job.timing {
        for i in 0..<33 {
            for k in 0..<job.x.count { pointer[k] = Float.nan }
            let ms = try dispatch(64)
            try require(referenceOutput == Data(bytes: out.contents(), count: job.x.count*4), "batched output differs from checked output")
            if i >= 3 {
                try require(ms.isFinite && ms > 0, "invalid GPU interval")
                intervals.append(ms)
            }
        }
    }
    let result: [String: Any] = ["output": values, "inputs_unchanged": true, "device": device.name,
                               "gpu_buffer_ms": intervals, "other_gpu_clients": "not_excluded"]
    let bytes = try JSONSerialization.data(withJSONObject: result)
    FileHandle.standardOutput.write(bytes)
}
do { try main() } catch {
    FileHandle.standardError.write(Data("\(error)\n".utf8)); exit(1)
}
