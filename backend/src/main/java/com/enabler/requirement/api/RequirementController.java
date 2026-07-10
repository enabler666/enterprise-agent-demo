package com.enabler.requirement.api;

import com.enabler.common.api.ApiResponse;
import com.enabler.common.api.PageResult;
import com.enabler.common.trace.TraceIdFilter;
import com.enabler.requirement.service.RequirementService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Pattern;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@Validated
@RestController
@RequestMapping("/api/requirements")
public class RequirementController {

    private final RequirementService service;

    public RequirementController(RequirementService service) {
        this.service = service;
    }

    @GetMapping("/{requirementNo}")
    public ApiResponse<RequirementDto> getByRequirementNo(
            @PathVariable @Pattern(regexp = "[A-Za-z0-9_-]+") String requirementNo,
            HttpServletRequest request) {
        return ApiResponse.success(
                service.getByRequirementNo(requirementNo), TraceIdFilter.from(request));
    }

    @GetMapping
    public ApiResponse<PageResult<RequirementDto>> search(
            @Valid @ModelAttribute RequirementQueryRequest query,
            HttpServletRequest request) {
        return ApiResponse.success(service.search(query), TraceIdFilter.from(request));
    }

    @GetMapping("/{requirementNo}/progress")
    public ApiResponse<RequirementProgressDto> getProgress(
            @PathVariable @Pattern(regexp = "[A-Za-z0-9_-]+") String requirementNo,
            HttpServletRequest request) {
        return ApiResponse.success(
                service.getProgress(requirementNo), TraceIdFilter.from(request));
    }
}
