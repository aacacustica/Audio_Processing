desire_sr = float(input("Enter the desired sample rate: "))

size_at_16k_hz = 29.0  # size in MB for 16k hz for 15 minutes
sample_rate_original = 16000  # original sample rate
sample_rate_new = desire_sr

print(type(sample_rate_new))
print(type(sample_rate_original))
print(type(size_at_16k_hz))


size_at_desire_sr = size_at_16k_hz * (sample_rate_new / sample_rate_original)
print(size_at_desire_sr, "MB")
