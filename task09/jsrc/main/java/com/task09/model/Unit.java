package com.task09.model;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.Data;
import software.amazon.awssdk.enhanced.dynamodb.mapper.annotations.DynamoDbBean;

@JsonIgnoreProperties(ignoreUnknown = true)
@DynamoDbBean
public class Unit {
    private String time;
    //private String interval;
    private String temperature_2m;
//    private String wind_speed_10m;
//    private String relative_humidity_2m;

    public String getTime() {
        
        return time;
    }

    public void setTime(String time) {
        this.time = time;
    }

//    public String getInterval() {
//        return interval;
//    }
//
//    public void setInterval(String interval) {
//        this.interval = interval;
//    }

    public String getTemperature_2m() {
        return temperature_2m;
    }

    public void setTemperature_2m(String temperature_2m) {
        this.temperature_2m = temperature_2m;
    }

//    public String getWind_speed_10m() {
//        return wind_speed_10m;
//    }
//
//    public void setWind_speed_10m(String wind_speed_10m) {
//        this.wind_speed_10m = wind_speed_10m;
//    }
//
//    public String getRelative_humidity_2m() {
//        return relative_humidity_2m;
//    }
//
//    public void setRelative_humidity_2m(String relative_humidity_2m) {
//        this.relative_humidity_2m = relative_humidity_2m;
//    }
}
