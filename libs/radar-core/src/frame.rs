//! Radar frame types and data structures.

/// Dimensions of a radar frame.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct FrameDimensions {
    /// Number of Doppler bins (rows).
    pub n_doppler: u32,
    /// Number of range bins (columns).
    pub n_range: u32,
}

impl FrameDimensions {
    /// Create new frame dimensions.
    pub fn new(n_doppler: u32, n_range: u32) -> Self {
        Self { n_doppler, n_range }
    }

    /// Total number of samples in the frame.
    pub fn total_samples(&self) -> usize {
        (self.n_doppler * self.n_range) as usize
    }

    /// Get dimensions as (rows, cols) tuple.
    pub fn as_tuple(&self) -> (usize, usize) {
        (self.n_doppler as usize, self.n_range as usize)
    }
}

/// Format of frame data values.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum FrameFormat {
    /// 32-bit floating point (native from Python).
    Float32,
    /// 8-bit unsigned integer (quantized for wire transport).
    UInt8,
    /// 16-bit unsigned integer (higher precision quantized).
    UInt16,
}

impl FrameFormat {
    /// Bytes per sample for this format.
    pub fn bytes_per_sample(&self) -> usize {
        match self {
            Self::Float32 => 4,
            Self::UInt8 => 1,
            Self::UInt16 => 2,
        }
    }

    /// Wire protocol value for this format.
    pub fn wire_value(&self) -> u8 {
        match self {
            Self::UInt8 => 0,
            Self::UInt16 => 1,
            Self::Float32 => 2,
        }
    }

    /// Parse format from wire protocol value.
    pub fn from_wire_value(value: u8) -> Option<Self> {
        match value {
            0 => Some(Self::UInt8),
            1 => Some(Self::UInt16),
            2 => Some(Self::Float32),
            _ => None,
        }
    }
}

/// Frame data storage.
#[derive(Debug, Clone)]
pub enum FrameData {
    /// 32-bit floating point data.
    Float32(Vec<f32>),
    /// 8-bit unsigned integer data.
    UInt8(Vec<u8>),
    /// 16-bit unsigned integer data.
    UInt16(Vec<u16>),
}

impl FrameData {
    /// Get the format of this data.
    pub fn format(&self) -> FrameFormat {
        match self {
            Self::Float32(_) => FrameFormat::Float32,
            Self::UInt8(_) => FrameFormat::UInt8,
            Self::UInt16(_) => FrameFormat::UInt16,
        }
    }

    /// Get the number of samples.
    pub fn len(&self) -> usize {
        match self {
            Self::Float32(v) => v.len(),
            Self::UInt8(v) => v.len(),
            Self::UInt16(v) => v.len(),
        }
    }

    /// Check if data is empty.
    pub fn is_empty(&self) -> bool {
        self.len() == 0
    }

    /// Get raw bytes for wire transport.
    pub fn as_bytes(&self) -> &[u8] {
        match self {
            Self::Float32(v) => bytemuck_slice(v),
            Self::UInt8(v) => v,
            Self::UInt16(v) => bytemuck_slice(v),
        }
    }
}

/// Helper to get byte slice from typed slice.
fn bytemuck_slice<T>(slice: &[T]) -> &[u8] {
    unsafe {
        std::slice::from_raw_parts(
            slice.as_ptr() as *const u8,
            slice.len() * std::mem::size_of::<T>(),
        )
    }
}

/// A radar frame with metadata.
///
/// Contains the Range-Doppler map data along with all metadata needed
/// for interpretation and display.
#[derive(Debug, Clone)]
pub struct RadarFrame {
    /// Frame dimensions.
    pub dimensions: FrameDimensions,
    /// Data format.
    pub format: FrameFormat,
    /// Raw data (row-major, Doppler x Range).
    /// For Float32: values in log10 scale [scale_min, scale_max].
    /// For UInt8: values 0-255 mapped to [scale_min, scale_max].
    pub data: FrameData,
    /// Minimum value in log10 scale.
    pub scale_min: f32,
    /// Maximum value in log10 scale.
    pub scale_max: f32,
    /// Minimum range covered (meters).
    pub range_min_m: f32,
    /// Maximum range covered (meters).
    pub range_max_m: f32,
    /// Minimum Doppler frequency (Hz).
    pub doppler_min_hz: f32,
    /// Maximum Doppler frequency (Hz).
    pub doppler_max_hz: f32,
    /// MTI filter enabled flag.
    pub mti_enabled: bool,
}

impl RadarFrame {
    /// Convert frame to UInt8 format for wire transport.
    pub fn to_u8(&self) -> RadarFrame {
        match &self.data {
            FrameData::UInt8(_) => self.clone(),
            FrameData::Float32(data) => {
                let scale = 255.0 / (self.scale_max - self.scale_min);
                let u8_data: Vec<u8> = data
                    .iter()
                    .map(|&v| ((v - self.scale_min) * scale).clamp(0.0, 255.0) as u8)
                    .collect();
                RadarFrame {
                    data: FrameData::UInt8(u8_data),
                    format: FrameFormat::UInt8,
                    ..self.clone()
                }
            }
            FrameData::UInt16(data) => {
                let u8_data: Vec<u8> = data.iter().map(|&v| (v >> 8) as u8).collect();
                RadarFrame {
                    data: FrameData::UInt8(u8_data),
                    format: FrameFormat::UInt8,
                    ..self.clone()
                }
            }
        }
    }

    /// Get value at (doppler, range) index as f32.
    pub fn get(&self, d: u32, r: u32) -> f32 {
        let idx = (d * self.dimensions.n_range + r) as usize;
        match &self.data {
            FrameData::Float32(data) => data[idx],
            FrameData::UInt8(data) => {
                let scale = (self.scale_max - self.scale_min) / 255.0;
                self.scale_min + data[idx] as f32 * scale
            }
            FrameData::UInt16(data) => {
                let scale = (self.scale_max - self.scale_min) / 65535.0;
                self.scale_min + data[idx] as f32 * scale
            }
        }
    }

    /// Get value at linear index as f32.
    pub fn get_linear(&self, idx: usize) -> f32 {
        match &self.data {
            FrameData::Float32(data) => data[idx],
            FrameData::UInt8(data) => {
                let scale = (self.scale_max - self.scale_min) / 255.0;
                self.scale_min + data[idx] as f32 * scale
            }
            FrameData::UInt16(data) => {
                let scale = (self.scale_max - self.scale_min) / 65535.0;
                self.scale_min + data[idx] as f32 * scale
            }
        }
    }

    /// Get the data as f32 slice (only if format is Float32).
    pub fn as_f32_slice(&self) -> Option<&[f32]> {
        match &self.data {
            FrameData::Float32(data) => Some(data),
            _ => None,
        }
    }

    /// Get the data as u8 slice (only if format is UInt8).
    pub fn as_u8_slice(&self) -> Option<&[u8]> {
        match &self.data {
            FrameData::UInt8(data) => Some(data),
            _ => None,
        }
    }

    /// Calculate the range in meters for a given range bin index.
    pub fn range_for_bin(&self, bin: u32) -> f32 {
        let fraction = bin as f32 / self.dimensions.n_range as f32;
        self.range_min_m + fraction * (self.range_max_m - self.range_min_m)
    }

    /// Calculate the Doppler frequency in Hz for a given Doppler bin index.
    pub fn doppler_for_bin(&self, bin: u32) -> f32 {
        let fraction = bin as f32 / self.dimensions.n_doppler as f32;
        self.doppler_min_hz + fraction * (self.doppler_max_hz - self.doppler_min_hz)
    }
}

impl Default for RadarFrame {
    fn default() -> Self {
        Self {
            dimensions: FrameDimensions::new(512, 30),
            format: FrameFormat::Float32,
            data: FrameData::Float32(vec![0.0; 512 * 30]),
            scale_min: 0.0,
            scale_max: 8.0,
            range_min_m: 0.0,
            range_max_m: 10.0,
            doppler_min_hz: -1000.0,
            doppler_max_hz: 1000.0,
            mti_enabled: false,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_dimensions() {
        let dims = FrameDimensions::new(512, 30);
        assert_eq!(dims.total_samples(), 15360);
        assert_eq!(dims.as_tuple(), (512, 30));
    }

    #[test]
    fn test_frame_quantization() {
        let frame = RadarFrame {
            dimensions: FrameDimensions::new(2, 2),
            format: FrameFormat::Float32,
            data: FrameData::Float32(vec![0.0, 4.0, 8.0, 2.0]),
            scale_min: 0.0,
            scale_max: 8.0,
            ..Default::default()
        };

        let u8_frame = frame.to_u8();
        match u8_frame.data {
            FrameData::UInt8(data) => {
                assert_eq!(data[0], 0); // 0.0 -> 0
                assert_eq!(data[1], 127); // 4.0 -> 127
                assert_eq!(data[2], 255); // 8.0 -> 255
                assert_eq!(data[3], 63); // 2.0 -> 63
            }
            _ => panic!("Expected UInt8 format"),
        }
    }

    #[test]
    fn test_frame_get() {
        let frame = RadarFrame {
            dimensions: FrameDimensions::new(2, 3),
            format: FrameFormat::Float32,
            data: FrameData::Float32(vec![1.0, 2.0, 3.0, 4.0, 5.0, 6.0]),
            ..Default::default()
        };

        assert_eq!(frame.get(0, 0), 1.0);
        assert_eq!(frame.get(0, 2), 3.0);
        assert_eq!(frame.get(1, 0), 4.0);
        assert_eq!(frame.get(1, 2), 6.0);
    }
}
