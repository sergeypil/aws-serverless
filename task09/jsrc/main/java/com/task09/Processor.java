package com.task09;

import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import com.amazonaws.xray.AWSXRay;
import com.amazonaws.xray.AWSXRayRecorderBuilder;
import com.amazonaws.xray.entities.Segment;
import com.amazonaws.xray.plugins.EC2Plugin;
import com.amazonaws.xray.strategy.sampling.LocalizedSamplingStrategy;
import com.syndicate.deployment.annotations.lambda.LambdaHandler;
import com.syndicate.deployment.model.RetentionSetting;
import com.task09.model.Forecast;
import com.task09.model.ForecastData;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.client.RestTemplate;
import software.amazon.awssdk.enhanced.dynamodb.DynamoDbEnhancedClient;
import software.amazon.awssdk.enhanced.dynamodb.DynamoDbTable;
import software.amazon.awssdk.enhanced.dynamodb.TableSchema;

import java.net.URL;
import java.util.Arrays;
import java.util.UUID;
import java.util.logging.Logger;

@LambdaHandler(lambdaName = "processor",
	roleName = "processor-role",
	logsExpiration = RetentionSetting.SYNDICATE_ALIASES_SPECIFIED
)
public class Processor implements RequestHandler<Object, String> {
	private static final Logger logger = Logger.getLogger(Processor.class.getName());
	RestTemplate restTemplate = new RestTemplate();
	private final DynamoDbEnhancedClient enhancedClient = DynamoDbEnhancedClient.create();
	private static final String TABLE_NAME = "cmtr-d7361a80-Weather-test";

	static {
		AWSXRayRecorderBuilder builder = AWSXRayRecorderBuilder.standard().withSamplingStrategy(new LocalizedSamplingStrategy());

		AWSXRay.setGlobalRecorder(builder.build());
	}

	public String handleRequest(Object request, Context context) {
		logger.info("Request: " + request);
		Segment subsegment = AWSXRay.beginSegment("handleRequest");
		try {
			String url = "https://api.open-meteo.com/v1/forecast?latitude=52.5200&longitude=13.4050&hourly=temperature_2m";

			HttpHeaders headers = new HttpHeaders();
			headers.setAccept(Arrays.asList(MediaType.APPLICATION_JSON));
			final HttpEntity<String> entity = new HttpEntity<String>(headers);

			ResponseEntity<Forecast> response = restTemplate.exchange(url, HttpMethod.GET, entity, Forecast.class);

			Forecast forecast = response.getBody();
			logger.info("Forecast: " + forecast);

			ForecastData forecastData = new ForecastData();
			forecastData.setId(UUID
								   .randomUUID()
								   .toString());
			forecastData.setForecast(forecast);
			logger.info("ForecastData: " + forecastData);

			DynamoDbTable<ForecastData> table = enhancedClient.table(TABLE_NAME, TableSchema.fromBean(ForecastData.class));
			table.putItem(forecastData);
			logger.info("Item saved to DynamoDB");
		} catch (Exception e) {
			AWSXRay
				.getCurrentSegment()
				.addException(e);
			throw e;
		} finally {
			AWSXRay.endSegment();
		}
		return "Lambda executed successfully!";
	}
}
