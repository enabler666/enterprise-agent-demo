package com.enabler.common.api;

import java.util.List;

public record PageResult<T>(
        List<T> items,
        long total,
        int page,
        int size,
        int totalPages) {

    public static <T> PageResult<T> of(List<T> items, long total, int page, int size) {
        int totalPages = total == 0 ? 0 : (int) ((total + size - 1) / size);
        return new PageResult<>(List.copyOf(items), total, page, size, totalPages);
    }
}
