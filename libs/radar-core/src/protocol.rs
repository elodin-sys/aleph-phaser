//! Wire protocol types for streaming radar frames.

use crate::frame::{FrameData, FrameFormat, RadarFrame};

/// Header for wire-format frames.
///
/// This is a compact binary header (32 bytes) that precedes frame payload data
/// when streaming over WebSocket or other transports.
#[derive(Debug, Clone, Copy)]
#[repr(C, packed)]
pub struct FrameHeader {
    /// Message type (0x01 = radar_frame).
    pub message_type: u8,
    /// Frame type (0x00 = range_doppler).
    pub frame_type: u8,
    /// Number of Doppler bins.
    pub n_doppler: u16,
    /// Number of range bins.
    pub n_range: u16,
    /// Value format (0=u8, 1=u16, 2=f32).
    pub value_format: u8,
    /// Flags (bit0=MTI enabled).
    pub flags: u8,
    /// Minimum scale value.
    pub scale_min: f32,
    /// Maximum scale value.
    pub scale_max: f32,
    /// Minimum range in meters.
    pub range_min_m: f32,
    /// Maximum range in meters.
    pub range_max_m: f32,
    /// Minimum Doppler in Hz.
    pub doppler_min_hz: f32,
    /// Maximum Doppler in Hz.
    pub doppler_max_hz: f32,
}

impl FrameHeader {
    /// Size of the header in bytes.
    pub const SIZE: usize = 32;

    /// Message type for radar frames.
    pub const MESSAGE_TYPE_RADAR_FRAME: u8 = 0x01;

    /// Frame type for range-Doppler maps.
    pub const FRAME_TYPE_RANGE_DOPPLER: u8 = 0x00;

    /// Flag bit for MTI enabled.
    pub const FLAG_MTI_ENABLED: u8 = 0x01;

    /// Create a new header from a radar frame.
    pub fn from_frame(frame: &RadarFrame) -> Self {
        Self {
            message_type: Self::MESSAGE_TYPE_RADAR_FRAME,
            frame_type: Self::FRAME_TYPE_RANGE_DOPPLER,
            n_doppler: frame.dimensions.n_doppler as u16,
            n_range: frame.dimensions.n_range as u16,
            value_format: frame.format.wire_value(),
            flags: if frame.mti_enabled {
                Self::FLAG_MTI_ENABLED
            } else {
                0
            },
            scale_min: frame.scale_min,
            scale_max: frame.scale_max,
            range_min_m: frame.range_min_m,
            range_max_m: frame.range_max_m,
            doppler_min_hz: frame.doppler_min_hz,
            doppler_max_hz: frame.doppler_max_hz,
        }
    }

    /// Serialize header to bytes.
    pub fn to_bytes(&self) -> [u8; Self::SIZE] {
        // Safe because repr(C, packed)
        unsafe { std::mem::transmute_copy(self) }
    }

    /// Deserialize header from bytes.
    pub fn from_bytes(bytes: &[u8; Self::SIZE]) -> Self {
        unsafe { std::mem::transmute_copy(bytes) }
    }

    /// Try to parse header from a byte slice.
    pub fn try_from_slice(bytes: &[u8]) -> Option<Self> {
        if bytes.len() < Self::SIZE {
            return None;
        }
        let arr: &[u8; Self::SIZE] = bytes[..Self::SIZE].try_into().ok()?;
        Some(Self::from_bytes(arr))
    }

    /// Check if MTI is enabled in flags.
    pub fn mti_enabled(&self) -> bool {
        self.flags & Self::FLAG_MTI_ENABLED != 0
    }

    /// Get the value format.
    pub fn format(&self) -> Option<FrameFormat> {
        FrameFormat::from_wire_value(self.value_format)
    }

    /// Calculate expected payload size in bytes.
    pub fn payload_size(&self) -> usize {
        let samples = self.n_doppler as usize * self.n_range as usize;
        match self.format() {
            Some(FrameFormat::UInt8) => samples,
            Some(FrameFormat::UInt16) => samples * 2,
            Some(FrameFormat::Float32) => samples * 4,
            None => 0,
        }
    }
}

/// Encoded frame ready for wire transport.
///
/// Contains the header and payload as separate components for flexible
/// transmission (e.g., can send header first to allow receiver to allocate).
pub struct EncodedFrame {
    /// Frame header.
    pub header: FrameHeader,
    /// Payload data (quantized to u8 by default).
    pub payload: Vec<u8>,
}

impl EncodedFrame {
    /// Create from a RadarFrame (converts to u8 format).
    pub fn from_frame(frame: &RadarFrame) -> Self {
        let u8_frame = frame.to_u8();
        let payload = match u8_frame.data {
            FrameData::UInt8(data) => data,
            _ => unreachable!("to_u8() always returns UInt8"),
        };

        let header = FrameHeader {
            message_type: FrameHeader::MESSAGE_TYPE_RADAR_FRAME,
            frame_type: FrameHeader::FRAME_TYPE_RANGE_DOPPLER,
            n_doppler: frame.dimensions.n_doppler as u16,
            n_range: frame.dimensions.n_range as u16,
            value_format: FrameFormat::UInt8.wire_value(),
            flags: if frame.mti_enabled {
                FrameHeader::FLAG_MTI_ENABLED
            } else {
                0
            },
            scale_min: frame.scale_min,
            scale_max: frame.scale_max,
            range_min_m: frame.range_min_m,
            range_max_m: frame.range_max_m,
            doppler_min_hz: frame.doppler_min_hz,
            doppler_max_hz: frame.doppler_max_hz,
        };

        Self { header, payload }
    }

    /// Serialize to bytes (header + payload).
    pub fn to_bytes(&self) -> Vec<u8> {
        let mut buf = Vec::with_capacity(FrameHeader::SIZE + self.payload.len());
        buf.extend_from_slice(&self.header.to_bytes());
        buf.extend_from_slice(&self.payload);
        buf
    }

    /// Total size in bytes.
    pub fn size(&self) -> usize {
        FrameHeader::SIZE + self.payload.len()
    }

    /// Try to decode from bytes.
    pub fn from_bytes(bytes: &[u8]) -> Option<Self> {
        if bytes.len() < FrameHeader::SIZE {
            return None;
        }

        let header = FrameHeader::try_from_slice(bytes)?;
        let expected_size = FrameHeader::SIZE + header.payload_size();

        if bytes.len() < expected_size {
            return None;
        }

        let payload = bytes[FrameHeader::SIZE..expected_size].to_vec();
        Some(Self { header, payload })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::frame::FrameDimensions;

    #[test]
    fn test_header_size() {
        assert_eq!(FrameHeader::SIZE, 32);
        assert_eq!(std::mem::size_of::<FrameHeader>(), 32);
    }

    #[test]
    fn test_header_roundtrip() {
        let header = FrameHeader {
            message_type: 0x01,
            frame_type: 0x00,
            n_doppler: 512,
            n_range: 30,
            value_format: 0,
            flags: 0x01,
            scale_min: 0.0,
            scale_max: 8.0,
            range_min_m: 0.0,
            range_max_m: 10.0,
            doppler_min_hz: -1000.0,
            doppler_max_hz: 1000.0,
        };

        let bytes = header.to_bytes();
        let decoded = FrameHeader::from_bytes(&bytes);

        // Copy packed struct fields to local variables to avoid alignment issues
        let n_doppler = decoded.n_doppler;
        let n_range = decoded.n_range;
        assert_eq!(n_doppler, 512);
        assert_eq!(n_range, 30);
        assert!(decoded.mti_enabled());
    }

    #[test]
    fn test_encoded_frame_size() {
        let frame = RadarFrame {
            dimensions: FrameDimensions::new(512, 30),
            format: FrameFormat::Float32,
            data: FrameData::Float32(vec![0.0; 512 * 30]),
            ..Default::default()
        };

        let encoded = EncodedFrame::from_frame(&frame);
        assert_eq!(encoded.size(), 32 + 512 * 30); // Header + u8 payload
    }

    #[test]
    fn test_encoded_frame_roundtrip() {
        let frame = RadarFrame {
            dimensions: FrameDimensions::new(4, 3),
            format: FrameFormat::Float32,
            data: FrameData::Float32(vec![0.0, 2.0, 4.0, 6.0, 8.0, 4.0, 2.0, 0.0, 4.0, 8.0, 6.0, 2.0]),
            scale_min: 0.0,
            scale_max: 8.0,
            mti_enabled: true,
            ..Default::default()
        };

        let encoded = EncodedFrame::from_frame(&frame);
        let bytes = encoded.to_bytes();
        let decoded = EncodedFrame::from_bytes(&bytes).unwrap();

        // Copy packed struct fields to local variables to avoid alignment issues
        let n_doppler = decoded.header.n_doppler;
        let n_range = decoded.header.n_range;
        assert_eq!(n_doppler, 4);
        assert_eq!(n_range, 3);
        assert!(decoded.header.mti_enabled());
        assert_eq!(decoded.payload.len(), 12);
    }
}
