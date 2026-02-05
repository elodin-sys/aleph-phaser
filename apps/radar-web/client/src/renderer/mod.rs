//! WebGPU renderer for radar visualization.

mod colormap;
mod pipeline;
mod texture;

use web_sys::HtmlCanvasElement;
use wgpu::util::DeviceExt;

pub use colormap::Colormap;
pub use pipeline::RenderPipeline;
pub use texture::RadarTexture;

/// Uniforms for the render shader.
#[repr(C)]
#[derive(Debug, Copy, Clone, bytemuck::Pod, bytemuck::Zeroable)]
pub struct Uniforms {
    /// Viewport width.
    pub width: f32,
    /// Viewport height.
    pub height: f32,
    /// Zoom level (1.0 = no zoom).
    pub zoom: f32,
    /// Pan X offset (normalized).
    pub pan_x: f32,
    /// Pan Y offset (normalized).
    pub pan_y: f32,
    /// Gain adjustment.
    pub gain: f32,
    /// Gamma correction.
    pub gamma: f32,
    /// Padding for alignment.
    pub _padding: f32,
}

impl Default for Uniforms {
    fn default() -> Self {
        Self {
            width: 800.0,
            height: 600.0,
            zoom: 1.0,
            pan_x: 0.0,
            pan_y: 0.0,
            gain: 1.0,
            gamma: 1.0,
            _padding: 0.0,
        }
    }
}

/// WebGPU renderer for radar visualization.
pub struct Renderer {
    device: wgpu::Device,
    queue: wgpu::Queue,
    surface: wgpu::Surface<'static>,
    surface_config: wgpu::SurfaceConfiguration,
    pipeline: RenderPipeline,
    radar_texture: RadarTexture,
    colormap_texture: texture::ColormapTexture,
    uniform_buffer: wgpu::Buffer,
    bind_group: wgpu::BindGroup,
    uniforms: Uniforms,
}

impl Renderer {
    /// Create a new renderer for the given canvas.
    pub async fn new(canvas: HtmlCanvasElement) -> Result<Self, String> {
        log::info!("Initializing WebGPU renderer");

        // Create wgpu instance
        let instance = wgpu::Instance::new(&wgpu::InstanceDescriptor {
            backends: wgpu::Backends::BROWSER_WEBGPU,
            ..Default::default()
        });

        // Create surface from canvas
        let surface = instance
            .create_surface(wgpu::SurfaceTarget::Canvas(canvas.clone()))
            .map_err(|e| format!("Failed to create surface: {}", e))?;

        // Request adapter
        let adapter = instance
            .request_adapter(&wgpu::RequestAdapterOptions {
                power_preference: wgpu::PowerPreference::HighPerformance,
                compatible_surface: Some(&surface),
                force_fallback_adapter: false,
            })
            .await
            .map_err(|e| format!("Failed to find suitable GPU adapter: {}", e))?;

        log::info!("Using adapter: {:?}", adapter.get_info().name);

        // Request device
        let (device, queue) = adapter
            .request_device(&wgpu::DeviceDescriptor {
                label: Some("Radar Device"),
                required_features: wgpu::Features::empty(),
                required_limits: wgpu::Limits::downlevel_webgl2_defaults(),
                memory_hints: wgpu::MemoryHints::Performance,
                trace: wgpu::Trace::Off,
            })
            .await
            .map_err(|e| format!("Failed to create device: {}", e))?;

        // Configure surface
        let width = canvas.width();
        let height = canvas.height();
        let surface_caps = surface.get_capabilities(&adapter);
        let surface_format = surface_caps
            .formats
            .iter()
            .copied()
            .find(|f| f.is_srgb())
            .unwrap_or(surface_caps.formats[0]);

        let surface_config = wgpu::SurfaceConfiguration {
            usage: wgpu::TextureUsages::RENDER_ATTACHMENT,
            format: surface_format,
            width,
            height,
            present_mode: wgpu::PresentMode::AutoVsync,
            alpha_mode: surface_caps.alpha_modes[0],
            view_formats: vec![],
            desired_maximum_frame_latency: 2,
        };
        surface.configure(&device, &surface_config);

        // Create render pipeline
        let pipeline = RenderPipeline::new(&device, surface_format);

        // Create radar texture (initial size, will be resized on first frame)
        let radar_texture = RadarTexture::new(&device, 512, 1800);

        // Create colormap texture
        let colormap_texture = texture::ColormapTexture::new(&device, &queue, Colormap::Inferno);

        // Create uniform buffer
        let uniforms = Uniforms {
            width: width as f32,
            height: height as f32,
            ..Default::default()
        };
        let uniform_buffer = device.create_buffer_init(&wgpu::util::BufferInitDescriptor {
            label: Some("Uniform Buffer"),
            contents: bytemuck::cast_slice(&[uniforms]),
            usage: wgpu::BufferUsages::UNIFORM | wgpu::BufferUsages::COPY_DST,
        });

        // Create bind group
        let bind_group = device.create_bind_group(&wgpu::BindGroupDescriptor {
            label: Some("Render Bind Group"),
            layout: &pipeline.bind_group_layout,
            entries: &[
                wgpu::BindGroupEntry {
                    binding: 0,
                    resource: uniform_buffer.as_entire_binding(),
                },
                wgpu::BindGroupEntry {
                    binding: 1,
                    resource: wgpu::BindingResource::TextureView(&radar_texture.view),
                },
                wgpu::BindGroupEntry {
                    binding: 2,
                    resource: wgpu::BindingResource::Sampler(&radar_texture.sampler),
                },
                wgpu::BindGroupEntry {
                    binding: 3,
                    resource: wgpu::BindingResource::TextureView(&colormap_texture.view),
                },
                wgpu::BindGroupEntry {
                    binding: 4,
                    resource: wgpu::BindingResource::Sampler(&colormap_texture.sampler),
                },
            ],
        });

        log::info!("WebGPU renderer initialized");

        Ok(Self {
            device,
            queue,
            surface,
            surface_config,
            pipeline,
            radar_texture,
            colormap_texture,
            uniform_buffer,
            bind_group,
            uniforms,
        })
    }

    /// Update the radar texture with new frame data.
    pub fn update_texture(&mut self, data: &[u8], n_doppler: usize, n_range: usize) {
        // Resize texture if dimensions changed
        if n_doppler != self.radar_texture.width as usize
            || n_range != self.radar_texture.height as usize
        {
            log::info!("Resizing texture to {}x{}", n_doppler, n_range);
            self.radar_texture = RadarTexture::new(&self.device, n_doppler as u32, n_range as u32);
            self.recreate_bind_group();
        }

        // Upload data
        self.radar_texture.write(&self.queue, data);
    }

    /// Recreate bind group after texture resize.
    fn recreate_bind_group(&mut self) {
        self.bind_group = self.device.create_bind_group(&wgpu::BindGroupDescriptor {
            label: Some("Render Bind Group"),
            layout: &self.pipeline.bind_group_layout,
            entries: &[
                wgpu::BindGroupEntry {
                    binding: 0,
                    resource: self.uniform_buffer.as_entire_binding(),
                },
                wgpu::BindGroupEntry {
                    binding: 1,
                    resource: wgpu::BindingResource::TextureView(&self.radar_texture.view),
                },
                wgpu::BindGroupEntry {
                    binding: 2,
                    resource: wgpu::BindingResource::Sampler(&self.radar_texture.sampler),
                },
                wgpu::BindGroupEntry {
                    binding: 3,
                    resource: wgpu::BindingResource::TextureView(&self.colormap_texture.view),
                },
                wgpu::BindGroupEntry {
                    binding: 4,
                    resource: wgpu::BindingResource::Sampler(&self.colormap_texture.sampler),
                },
            ],
        });
    }

    /// Render a frame.
    pub fn render(&mut self) {
        let output = match self.surface.get_current_texture() {
            Ok(output) => output,
            Err(wgpu::SurfaceError::Lost) => {
                self.surface.configure(&self.device, &self.surface_config);
                return;
            }
            Err(wgpu::SurfaceError::OutOfMemory) => {
                log::error!("Out of GPU memory");
                return;
            }
            Err(e) => {
                log::warn!("Surface error: {:?}", e);
                return;
            }
        };

        let view = output
            .texture
            .create_view(&wgpu::TextureViewDescriptor::default());

        let mut encoder = self
            .device
            .create_command_encoder(&wgpu::CommandEncoderDescriptor {
                label: Some("Render Encoder"),
            });

        {
            let mut render_pass = encoder.begin_render_pass(&wgpu::RenderPassDescriptor {
                label: Some("Render Pass"),
                color_attachments: &[Some(wgpu::RenderPassColorAttachment {
                    view: &view,
                    resolve_target: None,
                    ops: wgpu::Operations {
                        load: wgpu::LoadOp::Clear(wgpu::Color {
                            r: 0.1,
                            g: 0.1,
                            b: 0.15,
                            a: 1.0,
                        }),
                        store: wgpu::StoreOp::Store,
                    },
                })],
                depth_stencil_attachment: None,
                timestamp_writes: None,
                occlusion_query_set: None,
            });

            render_pass.set_pipeline(&self.pipeline.pipeline);
            render_pass.set_bind_group(0, &self.bind_group, &[]);
            render_pass.draw(0..6, 0..1); // Full-screen quad (2 triangles)
        }

        self.queue.submit(std::iter::once(encoder.finish()));
        output.present();
    }

    /// Update uniforms.
    pub fn set_uniforms(&mut self, uniforms: Uniforms) {
        self.uniforms = uniforms;
        self.queue
            .write_buffer(&self.uniform_buffer, 0, bytemuck::cast_slice(&[self.uniforms]));
    }

    /// Set zoom level.
    pub fn set_zoom(&mut self, zoom: f32) {
        self.uniforms.zoom = zoom.max(0.1).min(10.0);
        self.queue
            .write_buffer(&self.uniform_buffer, 0, bytemuck::cast_slice(&[self.uniforms]));
    }

    /// Set colormap.
    pub fn set_colormap(&mut self, colormap: Colormap) {
        self.colormap_texture = texture::ColormapTexture::new(&self.device, &self.queue, colormap);
        self.recreate_bind_group();
    }
}
