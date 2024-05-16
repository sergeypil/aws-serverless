package com.task06.model;

import software.amazon.awssdk.enhanced.dynamodb.mapper.annotations.DynamoDbBean;
import software.amazon.awssdk.enhanced.dynamodb.mapper.annotations.DynamoDbPartitionKey;

import java.util.Map;

@DynamoDbBean
public class AuditRecord {
    private String id;
    private String itemKey;
    private String modificationTime;
    private String updatedAttribute;
    private int oldValue;
    private Object newValue;
    @DynamoDbPartitionKey
    public String getId() { return id; }

    public void setId(String id) {
        this.id = id;
    }

    public String getItemKey() {
        return itemKey;
    }

    public void setItemKey(String itemKey) {
        this.itemKey = itemKey;
    }

    public String getModificationTime() {
        return modificationTime;
    }

    public void setModificationTime(String modificationTime) {
        this.modificationTime = modificationTime;
    }

    public String getUpdatedAttribute() {
        return updatedAttribute;
    }

    public void setUpdatedAttribute(String updatedAttribute) {
        this.updatedAttribute = updatedAttribute;
    }

    public int getOldValue() {
        return oldValue;
    }

    public void setOldValue(int oldValue) {
        this.oldValue = oldValue;
    }

    public Object getNewValue() {
        return newValue;
    }

    public void setNewValue(Object newValue) {
        this.newValue = newValue;
    }

    @Override
    public String toString() {
        return "AuditRecord{" +
            "id='" + id + '\'' +
            ", itemKey='" + itemKey + '\'' +
            ", modificationTime='" + modificationTime + '\'' +
            ", updatedAttribute='" + updatedAttribute + '\'' +
            ", oldValue=" + oldValue +
            ", newValue=" + newValue +
            '}';
    }
}