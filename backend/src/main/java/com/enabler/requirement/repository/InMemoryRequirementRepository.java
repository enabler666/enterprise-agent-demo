package com.enabler.requirement.repository;

import com.enabler.requirement.domain.Requirement;
import com.enabler.requirement.domain.RequirementQuery;
import com.enabler.requirement.domain.RequirementStatus;
import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.Optional;
import java.util.stream.Stream;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Repository;

@Repository
@Profile("!mysql")
public class InMemoryRequirementRepository implements RequirementRepository {

    private static final ZoneOffset ZONE = ZoneOffset.ofHours(8);
    private final List<Requirement> requirements = createRequirements();

    @Override
    public Optional<Requirement> findByRequirementNo(String requirementNo) {
        return requirements.stream()
                .filter(requirement -> requirement.requirementNo().equals(requirementNo))
                .findFirst();
    }

    @Override
    public List<Requirement> findAll(RequirementQuery query) {
        long offset = (long) query.page() * query.size();
        return filtered(query)
                .sorted(Comparator.comparing(Requirement::createdAt).reversed())
                .skip(offset)
                .limit(query.size())
                .toList();
    }

    @Override
    public long count(RequirementQuery query) {
        return filtered(query).count();
    }

    private Stream<Requirement> filtered(RequirementQuery query) {
        return requirements.stream()
                .filter(value -> exact(value.requirementNo(), query.requirementNo()))
                .filter(value -> contains(value.title(), query.title()))
                .filter(value -> exact(value.applicantId(), query.applicantId()))
                .filter(value -> exact(value.applicantName(), query.applicantName()))
                .filter(value -> exact(value.department(), query.department()))
                .filter(value -> query.status() == null || value.status() == query.status())
                .filter(value -> query.createdFrom() == null
                        || !value.createdAt().isBefore(query.createdFrom()))
                .filter(value -> query.createdTo() == null
                        || !value.createdAt().isAfter(query.createdTo()));
    }

    private boolean exact(String value, String expected) {
        return expected == null || expected.isBlank() || value.equals(expected.trim());
    }

    private boolean contains(String value, String expected) {
        return expected == null || expected.isBlank()
                || value.toLowerCase(Locale.ROOT).contains(expected.trim().toLowerCase(Locale.ROOT));
    }

    private static List<Requirement> createRequirements() {
        return List.of(
                item(1L, "XQ202607001", "新增生产服务器", "采购两台生产服务器", "U001", "张伟",
                        "信息技术部", "设备采购", RequirementStatus.PENDING_APPROVAL, "部门负责人审批",
                        "2026-08-15", "2026-07-01T09:00:00+08:00"),
                item(2L, "XQ202607002", "服务器扩容申请", "扩容现有应用服务器", "U002", "李娜",
                        "信息技术部", "资源扩容", RequirementStatus.EXECUTING, "执行中",
                        "2026-07-31", "2026-07-02T10:30:00+08:00"),
                item(3L, "XQ202607003", "采购办公电脑", "采购十台办公电脑", "U003", "王强",
                        "行政部", "设备采购", RequirementStatus.DRAFT, "草稿",
                        "2026-08-20", "2026-07-03T14:00:00+08:00"),
                item(4L, "XQ202607004", "财务系统报表优化", "优化月结报表", "U004", "赵敏",
                        "财务部", "系统优化", RequirementStatus.APPROVED, "等待执行",
                        "2026-08-10", "2026-07-04T11:00:00+08:00"),
                item(5L, "XQ202607005", "招聘系统接口改造", "对接新招聘平台", "U005", "陈晨",
                        "人力资源部", "系统改造", RequirementStatus.REJECTED, "部门负责人审批",
                        "2026-09-01", "2026-07-05T15:20:00+08:00"),
                item(6L, "XQ202607006", "测试服务器申请", "申请自动化测试服务器", "U006", "周洋",
                        "研发部", "资源申请", RequirementStatus.PENDING_APPROVAL, "采购审批",
                        "2026-08-01", "2026-07-06T09:40:00+08:00"),
                item(7L, "XQ202607007", "客户数据看板", "建设客户运营数据看板", "U007", "吴婷",
                        "市场部", "数据产品", RequirementStatus.CANCELLED, "已取消",
                        "2026-08-30", "2026-07-07T13:10:00+08:00"),
                item(8L, "XQ202606001", "服务器安全加固", "完成互联网服务器安全加固", "U001", "张伟",
                        "信息技术部", "安全整改", RequirementStatus.COMPLETED, "已完成",
                        "2026-06-30", "2026-06-01T09:00:00+08:00"),
                item(9L, "XQ202606002", "差旅制度更新", "更新国内差旅标准", "U008", "孙悦",
                        "行政部", "制度修订", RequirementStatus.COMPLETED, "已完成",
                        "2026-06-25", "2026-06-05T10:00:00+08:00"),
                item(10L, "XQ202606003", "供应商门户优化", "优化供应商注册流程", "U009", "刘凯",
                        "采购部", "系统优化", RequirementStatus.EXECUTING, "执行中",
                        "2026-07-20", "2026-06-10T16:00:00+08:00"),
                item(11L, "XQ202605001", "合同模板更新", "更新采购合同标准模板", "U010", "何静",
                        "法务部", "模板修订", RequirementStatus.COMPLETED, "已完成",
                        "2026-05-31", "2026-05-02T08:30:00+08:00"),
                item(12L, "XQ202605002", "营销活动预算申请", "申请夏季营销活动预算", "U007", "吴婷",
                        "市场部", "预算申请", RequirementStatus.REJECTED, "部门负责人审批",
                        "2026-06-15", "2026-05-10T14:30:00+08:00"));
    }

    private static Requirement item(
            Long id, String no, String title, String description, String applicantId,
            String applicantName, String department, String type, RequirementStatus status,
            String currentNode, String expectedDate, String createdAt) {
        OffsetDateTime created = OffsetDateTime.parse(createdAt);
        return new Requirement(id, no, title, description, applicantId, applicantName, department,
                type, status, currentNode, LocalDate.parse(expectedDate), created,
                created.plusDays(2).withOffsetSameInstant(ZONE));
    }
}
