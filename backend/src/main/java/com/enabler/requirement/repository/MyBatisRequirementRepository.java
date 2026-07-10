package com.enabler.requirement.repository;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.enabler.requirement.domain.Requirement;
import com.enabler.requirement.domain.RequirementQuery;
import com.enabler.requirement.infrastructure.mybatis.RequirementEntity;
import com.enabler.requirement.infrastructure.mybatis.RequirementMapper;
import java.util.List;
import java.util.Optional;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Repository;

@Repository
@Profile("mysql")
public class MyBatisRequirementRepository implements RequirementRepository {

    private final RequirementMapper mapper;

    public MyBatisRequirementRepository(RequirementMapper mapper) {
        this.mapper = mapper;
    }

    @Override
    public Optional<Requirement> findByRequirementNo(String requirementNo) {
        LambdaQueryWrapper<RequirementEntity> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(RequirementEntity::getRequirementNo, requirementNo).last("LIMIT 1");
        return Optional.ofNullable(mapper.selectOne(wrapper)).map(this::toDomain);
    }

    @Override
    public List<Requirement> findAll(RequirementQuery query) {
        Page<RequirementEntity> page = new Page<>(query.page() + 1L, query.size(), false);
        return mapper.selectPage(page, createWrapper(query).orderByDesc(RequirementEntity::getCreatedAt))
                .getRecords().stream()
                .map(this::toDomain)
                .toList();
    }

    @Override
    public long count(RequirementQuery query) {
        return mapper.selectCount(createWrapper(query));
    }

    private LambdaQueryWrapper<RequirementEntity> createWrapper(RequirementQuery query) {
        LambdaQueryWrapper<RequirementEntity> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(hasText(query.requirementNo()), RequirementEntity::getRequirementNo,
                        trimmed(query.requirementNo()))
                .like(hasText(query.title()), RequirementEntity::getTitle, trimmed(query.title()))
                .eq(hasText(query.applicantId()), RequirementEntity::getApplicantId,
                        trimmed(query.applicantId()))
                .eq(hasText(query.applicantName()), RequirementEntity::getApplicantName,
                        trimmed(query.applicantName()))
                .eq(hasText(query.department()), RequirementEntity::getDepartment,
                        trimmed(query.department()))
                .eq(query.status() != null, RequirementEntity::getStatus, query.status())
                .ge(query.createdFrom() != null, RequirementEntity::getCreatedAt, query.createdFrom())
                .le(query.createdTo() != null, RequirementEntity::getCreatedAt, query.createdTo());
        return wrapper;
    }

    private boolean hasText(String value) {
        return value != null && !value.isBlank();
    }

    private String trimmed(String value) {
        return value == null ? null : value.trim();
    }

    private Requirement toDomain(RequirementEntity value) {
        return new Requirement(
                value.getId(), value.getRequirementNo(), value.getTitle(), value.getDescription(),
                value.getApplicantId(), value.getApplicantName(), value.getDepartment(),
                value.getType(), value.getStatus(), value.getCurrentNode(),
                value.getExpectedCompletionDate(), value.getCreatedAt(), value.getUpdatedAt());
    }
}
