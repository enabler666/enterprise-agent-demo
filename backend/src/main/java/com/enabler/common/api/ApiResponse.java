package com.enabler.common.api;

public record ApiResponse<T>(
        boolean success,
        String code,
        String message,
        T data,
        String traceId) {

    public static <T> ApiResponse<T> success(T data, String traceId) {
        return new ApiResponse<>(true, "OK", "查询成功", data, traceId);
    }

    public static <T> ApiResponse<T> failure(
            String code, String message, T data, String traceId) {
        return new ApiResponse<>(false, code, message, data, traceId);
    }
}
