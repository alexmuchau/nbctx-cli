duplicate_numbers = [3, 5, 8, 13, 21]
duplicate_scale = 2
duplicate_scaled = [value * duplicate_scale for value in duplicate_numbers]
duplicate_roots = [round(math.sqrt(value), 2) for value in duplicate_scaled]
duplicate_offset = 10
duplicate_adjusted = [value + duplicate_offset for value in duplicate_scaled]
duplicate_summary = {
    "count": len(duplicate_numbers),
    "average_scaled": mean(duplicate_scaled),
    "average_adjusted": mean(duplicate_adjusted),
    "largest_root": max(duplicate_roots),
}
