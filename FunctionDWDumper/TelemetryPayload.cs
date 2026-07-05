namespace FunctionDWDumper;

public class TelemetryPayload
{
    public string DeviceId { get; set; } = string.Empty;
    public string Timestamp { get; set; } = string.Empty;
    public double WindSpeed { get; set; }
    public double GeneratedPower { get; set; }
    public double TurbineSpeed { get; set; }
}