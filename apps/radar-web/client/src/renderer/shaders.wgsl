// WebGPU Shader for Radar Visualization
// Renders range-Doppler map with colormap lookup, zoom/pan, and grid overlay

struct Uniforms {
    width: f32,
    height: f32,
    zoom: f32,
    pan_x: f32,
    pan_y: f32,
    gain: f32,
    gamma: f32,
    _padding: f32,
};

struct VertexOutput {
    @builtin(position) position: vec4<f32>,
    @location(0) tex_coord: vec2<f32>,
};

@group(0) @binding(0)
var<uniform> uniforms: Uniforms;

@group(0) @binding(1)
var radar_texture: texture_2d<f32>;

@group(0) @binding(2)
var radar_sampler: sampler;

@group(0) @binding(3)
var colormap_texture: texture_1d<f32>;

@group(0) @binding(4)
var colormap_sampler: sampler;

// Full-screen quad vertices (2 triangles, 6 vertices)
var<private> POSITIONS: array<vec2<f32>, 6> = array<vec2<f32>, 6>(
    vec2<f32>(-1.0, -1.0),
    vec2<f32>( 1.0, -1.0),
    vec2<f32>( 1.0,  1.0),
    vec2<f32>(-1.0, -1.0),
    vec2<f32>( 1.0,  1.0),
    vec2<f32>(-1.0,  1.0),
);

var<private> TEX_COORDS: array<vec2<f32>, 6> = array<vec2<f32>, 6>(
    vec2<f32>(0.0, 1.0),
    vec2<f32>(1.0, 1.0),
    vec2<f32>(1.0, 0.0),
    vec2<f32>(0.0, 1.0),
    vec2<f32>(1.0, 0.0),
    vec2<f32>(0.0, 0.0),
);

@vertex
fn vs_main(@builtin(vertex_index) vertex_index: u32) -> VertexOutput {
    var out: VertexOutput;
    out.position = vec4<f32>(POSITIONS[vertex_index], 0.0, 1.0);
    out.tex_coord = TEX_COORDS[vertex_index];
    return out;
}

@fragment
fn fs_main(in: VertexOutput) -> @location(0) vec4<f32> {
    // Apply zoom and pan
    let center = vec2<f32>(0.5, 0.5);
    let offset = vec2<f32>(uniforms.pan_x, uniforms.pan_y);
    var uv = (in.tex_coord - center) / uniforms.zoom + center + offset;

    // Clamp to valid texture range
    uv = clamp(uv, vec2<f32>(0.0), vec2<f32>(1.0));

    // Sample radar intensity (R channel from R8 texture)
    let intensity = textureSample(radar_texture, radar_sampler, uv).r;

    // Apply gain and gamma correction
    let adjusted = pow(intensity * uniforms.gain, uniforms.gamma);
    let normalized = clamp(adjusted, 0.0, 1.0);

    // Look up color from colormap
    let color = textureSample(colormap_texture, colormap_sampler, normalized);

    // Optional grid overlay
    let grid_color = draw_grid(in.tex_coord, uv);

    // Blend grid on top
    return mix(color, grid_color, grid_color.a * 0.3);
}

// Draw grid lines
fn draw_grid(screen_uv: vec2<f32>, radar_uv: vec2<f32>) -> vec4<f32> {
    let grid_spacing = 0.1;
    let line_width = 0.002 * uniforms.zoom;

    // Major grid lines
    let grid_x = abs(fract(radar_uv.x / grid_spacing + 0.5) - 0.5);
    let grid_y = abs(fract(radar_uv.y / grid_spacing + 0.5) - 0.5);

    let line_x = smoothstep(line_width, 0.0, grid_x * grid_spacing);
    let line_y = smoothstep(line_width, 0.0, grid_y * grid_spacing);

    let alpha = max(line_x, line_y);

    // Center crosshair (stronger)
    let center_x = abs(radar_uv.x - 0.5);
    let center_y = abs(radar_uv.y - 0.5);
    let crosshair = smoothstep(line_width * 2.0, 0.0, min(center_x, center_y));

    return vec4<f32>(0.5, 0.5, 0.5, max(alpha, crosshair * 0.5));
}
