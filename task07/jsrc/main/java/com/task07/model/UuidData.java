package com.task07.model;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

public class UuidData {
    private final List<String> ids;

    @JsonCreator
    public UuidData(@JsonProperty("uuids") List<String> ids) {
        this.ids = ids;
    }

    public List<String> getIds() {
        return ids;
    }
}