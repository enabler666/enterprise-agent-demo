package com.enabler.requirement.service;

import com.enabler.common.api.PageResult;
import com.enabler.requirement.api.RequirementDto;
import com.enabler.requirement.api.RequirementProgressDto;
import com.enabler.requirement.api.RequirementQueryRequest;
import com.enabler.requirement.domain.Requirement;
import com.enabler.requirement.domain.RequirementQuery;
import com.enabler.requirement.exception.RequirementNotFoundException;
import com.enabler.requirement.repository.RequirementRepository;
import java.util.List;
import org.springframework.stereotype.Service;

@Service
public class RequirementService {

    private final RequirementRepository repository;

    public RequirementService(RequirementRepository repository) {
        this.repository = repository;
    }

    public RequirementDto getByRequirementNo(String requirementNo) {
        return toDto(getRequired(requirementNo));
    }

    public PageResult<RequirementDto> search(RequirementQueryRequest request) {
        validateTimeRange(request);
        RequirementQuery query = new RequirementQuery(
                request.requirementNo(), request.title(), request.applicantId(),
                request.applicantName(), request.department(), request.status(),
                request.createdFrom(), request.createdTo(), request.resolvedPage(),
                request.resolvedSize());
        List<RequirementDto> items = repository.findAll(query).stream()
                .map(this::toDto)
                .toList();
        return PageResult.of(items, repository.count(query), query.page(), query.size());
    }

    public RequirementProgressDto getProgress(String requirementNo) {
        Requirement value = getRequired(requirementNo);
        return new RequirementProgressDto(
                value.requirementNo(), value.title(), value.status(), value.currentNode(),
                value.createdAt(), value.updatedAt(), value.expectedCompletionDate());
    }

    private Requirement getRequired(String requirementNo) {
        return repository.findByRequirementNo(requirementNo)
                .orElseThrow(() -> new RequirementNotFoundException(requirementNo));
    }

    private void validateTimeRange(RequirementQueryRequest request) {
        if (request.createdFrom() != null && request.createdTo() != null
                && request.createdFrom().isAfter(request.createdTo())) {
            throw new IllegalArgumentException("createdFrom must not be after createdTo");
        }
    }

    private RequirementDto toDto(Requirement value) {
        return new RequirementDto(
                value.id(), value.requirementNo(), value.title(), value.description(),
                value.applicantId(), value.applicantName(), value.department(), value.type(),
                value.status(), value.currentNode(), value.expectedCompletionDate(),
                value.createdAt(), value.updatedAt());
    }
}
