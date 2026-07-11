package com.enabler.common.exception;

import com.enabler.common.api.ApiResponse;
import com.enabler.common.trace.TraceIdFilter;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.ConstraintViolationException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.MissingServletRequestParameterException;
import org.springframework.web.method.annotation.HandlerMethodValidationException;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    @ExceptionHandler(BusinessException.class)
    public ResponseEntity<ApiResponse<Void>> handleBusinessException(
            BusinessException exception, HttpServletRequest request) {
        // 业务异常映射为稳定的 ApiResponse；Python Client 据此区分“无结果”和协议/网络故障。
        String traceId = TraceIdFilter.from(request);
        log.warn("Business exception, traceId={}, code={}, message={}",
                traceId, exception.getCode(), exception.getMessage());
        return ResponseEntity.status(HttpStatus.NOT_FOUND)
                .body(ApiResponse.failure(exception.getCode(), exception.getMessage(), null, traceId));
    }

    @ExceptionHandler({
            MethodArgumentNotValidException.class,
            ConstraintViolationException.class,
            HandlerMethodValidationException.class,
            MethodArgumentTypeMismatchException.class,
            MissingServletRequestParameterException.class,
            IllegalArgumentException.class
    })
    public ResponseEntity<ApiResponse<Void>> handleValidationException(
            Exception exception, HttpServletRequest request) {
        String traceId = TraceIdFilter.from(request);
        log.warn("Validation failed, traceId={}, message={}", traceId, exception.getMessage());
        return ResponseEntity.badRequest()
                .body(ApiResponse.failure("INVALID_ARGUMENT", "请求参数不合法", null, traceId));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiResponse<Void>> handleUnexpectedException(
            Exception exception, HttpServletRequest request) {
        String traceId = TraceIdFilter.from(request);
        log.error("Unexpected exception, traceId={}", traceId, exception);
        return ResponseEntity.internalServerError()
                .body(ApiResponse.failure("INTERNAL_ERROR", "系统内部错误", null, traceId));
    }
}
