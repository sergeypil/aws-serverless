package com.task06;

import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import com.amazonaws.services.lambda.runtime.events.DynamodbEvent;
import com.amazonaws.services.lambda.runtime.events.DynamodbEvent.DynamodbStreamRecord;
import com.amazonaws.services.lambda.runtime.events.models.dynamodb.AttributeValue;
import com.syndicate.deployment.annotations.events.DynamoDbTriggerEventSource;
import com.syndicate.deployment.annotations.lambda.LambdaHandler;
import com.syndicate.deployment.model.RetentionSetting;
import com.task06.model.AuditRecord;
import software.amazon.awssdk.enhanced.dynamodb.DynamoDbEnhancedClient;
import software.amazon.awssdk.enhanced.dynamodb.DynamoDbTable;
import software.amazon.awssdk.enhanced.dynamodb.TableSchema;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.logging.Logger;

@LambdaHandler(lambdaName = "audit_producer",
			   roleName = "audit_producer-role",
			   logsExpiration = RetentionSetting.SYNDICATE_ALIASES_SPECIFIED
)
@DynamoDbTriggerEventSource(targetTable = "Configuration", batchSize = 1)
public class AuditProducer implements RequestHandler<DynamodbEvent, Void> {

	private static final Logger logger = Logger.getLogger(AuditProducer.class.getName());
	private static final String INSERT_EVENT = "INSERT";
	private static final String MODIFY_EVENT = "MODIFY";
	private static final String TABLE_AUDIT = "cmtr-d7361a80-Audit-test";
	private final DynamoDbEnhancedClient enhancedClient = DynamoDbEnhancedClient.create();

	public Void handleRequest(DynamodbEvent dynamodbEvent, Context context) {
		logger.info("Received event: " + dynamodbEvent);
		List<DynamodbStreamRecord> records = dynamodbEvent.getRecords();

		DynamoDbTable<AuditRecord> table = enhancedClient.table(TABLE_AUDIT, TableSchema.fromBean(AuditRecord.class));

		for (DynamodbEvent.DynamodbStreamRecord record : records) {
			AuditRecord auditRecord = new AuditRecord();
			auditRecord.setId(UUID.randomUUID().toString());
			auditRecord.setModificationTime(LocalDateTime.now().format(DateTimeFormatter.ISO_DATE_TIME));
			Map<String, AttributeValue> newImage = record.getDynamodb().getNewImage();
			logger.info("New image: " + newImage);
			
			if (record.getEventName().equals(INSERT_EVENT)) {
				logger.info("Processing INSERT event");
				auditRecord.setItemKey(newImage.get("key").getS());
				auditRecord.setNewValue(Map.of("key", newImage.get("key").getS(), "value", newImage.get("value").getN()));
			}

			if (record.getEventName().equals(MODIFY_EVENT)) {
				logger.info("Processing MODIFY event");
				Map<String, AttributeValue> oldImage = record.getDynamodb().getOldImage();
				auditRecord.setItemKey(oldImage.get("key").getS());
				auditRecord.setUpdatedAttribute("value");
				auditRecord.setOldValue(Integer.valueOf(oldImage.get("value").getN()));
				auditRecord.setNewValue(Integer.valueOf(newImage.get("value").getN()));
			}
			logger.info("Saving audit record: " + auditRecord);
			table.putItem(auditRecord);
		}
		return null;
	}
}