#include <metal_stdlib>
using namespace metal;
// Original integration baseline, one SIMD group per row; no strong-baseline claim.
kernel void rmsnorm(device const float* x [[buffer(0)]],
                    device const float* weight [[buffer(1)]],
                    device float* out [[buffer(2)]],
                    constant uint& columns [[buffer(3)]],
                    constant float& epsilon [[buffer(4)]],
                    uint row [[threadgroup_position_in_grid]],
                    uint lane [[thread_index_in_simdgroup]]) {
    float sum = 0;
    for (uint c = lane; c < columns; c += 32) sum += x[row*columns+c]*x[row*columns+c];
    float inv = 1.0f / sqrt(simd_sum(sum)/float(columns)+epsilon);
    for (uint c = lane; c < columns; c += 32) out[row*columns+c] = x[row*columns+c]*inv*weight[c];
}
