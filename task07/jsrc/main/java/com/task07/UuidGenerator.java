package com.task07;

import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import com.amazonaws.services.s3.AmazonS3;
import com.amazonaws.services.s3.AmazonS3ClientBuilder;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.syndicate.deployment.annotations.events.EventBridgeRuleSource;
import com.syndicate.deployment.annotations.lambda.LambdaHandler;
import com.syndicate.deployment.model.RetentionSetting;
import com.task07.model.UuidData;

import java.time.Instant;
import java.util.List;
import java.util.UUID;
import java.util.logging.Logger;
import java.util.stream.Collectors;
import java.util.stream.IntStream;

@LambdaHandler(lambdaName = "uuid_generator",
	roleName = "uuid_generator-role",
	logsExpiration = RetentionSetting.SYNDICATE_ALIASES_SPECIFIED
)
@EventBridgeRuleSource(targetRule = "uuid_trigger")
public class UuidGenerator implements RequestHandler<Object, String> {

	private static final Logger logger = Logger.getLogger(UuidGenerator.class.getName());
	private static final ObjectMapper mapper = new ObjectMapper();
	private static final AmazonS3 s3Client = AmazonS3ClientBuilder.standard().build();

	public String handleRequest(Object request, Context context) {
		logger.info("Lambda is invoked.");
		
		List<String> uuids = IntStream
			.range(0, 10)
			.mapToObj(i -> UUID.randomUUID().toString())
			.collect(Collectors.toList());
		
		UuidData uuidData = new UuidData(uuids);
		
        String jsonData;
        try {
            jsonData = mapper.writeValueAsString(uuidData);
        } catch (JsonProcessingException e) {
            throw new RuntimeException(e);
        }

        String s3FileName = Instant.now() + ".json";
		
		logger.info("Uploading data to S3...");
		s3Client.putObject("uuid-storage", s3FileName, jsonData);
		logger.info("Data uploaded to S3.");
		
		return "Lambda is finished.";
	}
}