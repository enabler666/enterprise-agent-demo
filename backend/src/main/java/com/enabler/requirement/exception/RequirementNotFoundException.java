package com.enabler.requirement.exception;

import com.enabler.common.exception.BusinessException;

public class RequirementNotFoundException extends BusinessException {

    public RequirementNotFoundException(String requirementNo) {
        super("REQUIREMENT_NOT_FOUND", "未找到需求 " + requirementNo);
    }
}
