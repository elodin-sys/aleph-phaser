fn main() {
    // PyO3 configuration is only needed when the python feature is enabled
    #[cfg(feature = "python")]
    {
        // PyO3 configuration is automatic with the auto-initialize feature
        // No additional link args needed for embedding Python
    }
}
