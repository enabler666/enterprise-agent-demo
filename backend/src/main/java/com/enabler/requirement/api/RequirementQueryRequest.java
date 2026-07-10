package com.enabler.requirement.api;

import com.enabler.requirement.domain.RequirementStatus;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import java.time.OffsetDateTime;
import org.springframework.format.annotation.DateTimeFormat;

public record RequirementQueryRequest(
        String requirementNo,
        String title,
        String applicantId,
        String applicantName,
        String department,
        RequirementStatus status,
        @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) OffsetDateTime createdFrom,
        @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) OffsetDateTime createdTo,
        @Min(0) Integer page,
        @Min(1) @Max(100) Integer size) {

    public int resolvedPage() {
        return page == null ? 0 : page;
    }

    public int resolvedSize() {
        return size == null ? 20 : size;
    }
}
