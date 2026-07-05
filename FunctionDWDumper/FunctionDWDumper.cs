using System;
using System.Text.Json;
using System.Threading.Tasks;
using Azure.Data.Tables;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Extensions.Logging;
using Azure.Messaging.EventHubs;

namespace FunctionDWDumper;

public class FunctionDWDumper
{
    private readonly ILogger<FunctionDWDumper> _logger;

    public FunctionDWDumper(ILogger<FunctionDWDumper> logger)
    {
        _logger = logger;
    }

[Function("FunctionDWDumper")]
public async Task Run(
    [EventHubTrigger(
        "turbine-telemetry",
        Connection = "EventHubConnection")]
    EventData[] events)
{
    foreach (var evt in events)
    {
        string eventData = evt.EventBody.ToString();

        _logger.LogInformation(
            "Event received: {eventData}",
            eventData);

        var telemetry = JsonSerializer.Deserialize<TelemetryPayload>(
            eventData,
            new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            });

        if (telemetry == null)
            continue;

        string status =
            telemetry.WindSpeed > 15 &&
            telemetry.GeneratedPower < 5
            ? "URGENT"
            : "HEALTHY";

        string storageConnectionString =
            Environment.GetEnvironmentVariable(
                "AzureWebJobsStorage")!;

        var tableClient = new TableClient(
            storageConnectionString,
            "TurbineMetrics");

        await tableClient.CreateIfNotExistsAsync();

        var entity = new TableEntity(
            telemetry.DeviceId,
            Guid.NewGuid().ToString())
        {
            { "WindSpeed", telemetry.WindSpeed },
            { "GeneratedPower", telemetry.GeneratedPower },
            { "TurbineSpeed", telemetry.TurbineSpeed },
            { "Status", status }
        };

        await tableClient.AddEntityAsync(entity);

        _logger.LogInformation(
            "Saved: {device} {status}",
            telemetry.DeviceId,
            status);
    }
}
}