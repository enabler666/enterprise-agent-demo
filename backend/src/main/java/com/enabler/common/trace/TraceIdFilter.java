package com.enabler.common.trace;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.UUID;
import org.slf4j.MDC;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

@Component
public class TraceIdFilter extends OncePerRequestFilter {

    public static final String HEADER_NAME = "X-Trace-Id";
    public static final String ATTRIBUTE_NAME = TraceIdFilter.class.getName() + ".traceId";

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain) throws ServletException, IOException {
        String headerTraceId = request.getHeader(HEADER_NAME);
        String traceId = headerTraceId == null || headerTraceId.isBlank()
                ? UUID.randomUUID().toString()
                : headerTraceId.trim();
        request.setAttribute(ATTRIBUTE_NAME, traceId);
        response.setHeader(HEADER_NAME, traceId);
        MDC.put("traceId", traceId);
        try {
            filterChain.doFilter(request, response);
        } finally {
            MDC.remove("traceId");
        }
    }

    public static String from(HttpServletRequest request) {
        Object value = request.getAttribute(ATTRIBUTE_NAME);
        return value == null ? "unknown" : value.toString();
    }
}
