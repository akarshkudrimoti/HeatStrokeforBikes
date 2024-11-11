import HealthKit
import HomeKit

class HeatStrokeMonitor {
    let healthStore = HKHealthStore()
    let homeManager = HMHomeManager()
    var baselineTemperature: Double = 98.6 // Example baseline in Fahrenheit
    var temperatureThreshold: Double = 104.0
    var fanAccessory: HMAccessory?

    init() {
        requestHealthDataAuthorization()
        findFanAccessory()
    }

    func requestHealthDataAuthorization() {
        let bodyTempType = HKObjectType.quantityType(forIdentifier: .bodyTemperature)!
        let heartRateType = HKObjectType.quantityType(forIdentifier: .heartRate)!

        healthStore.requestAuthorization(toShare: [], read: [bodyTempType, heartRateType]) { (success, error) in
            if success {
                self.startMonitoring()
            }
        }
    }

    func startMonitoring() {
        // Periodically fetch data and check thresholds
        Timer.scheduledTimer(withTimeInterval: 60, repeats: true) { timer in
            self.checkHeatStrokeRisk()
        }
    }

    func checkHeatStrokeRisk() {
        // Fetch the latest body temperature and heart rate from HealthKit
        fetchLatestTemperature { temperature in
            if let temp = temperature, temp >= self.temperatureThreshold {
                self.turnOnFan()
            } else {
                self.turnOffFan()
            }
        }
    }

    func fetchLatestTemperature(completion: @escaping (Double?) -> Void) {
        let bodyTempType = HKObjectType.quantityType(forIdentifier: .bodyTemperature)!

        let query = HKSampleQuery(sampleType: bodyTempType, predicate: nil, limit: 1, sortDescriptors: [.init(keyPath: #keyPath(HKSample.startDate), ascending: false)]) { (query, samples, error) in
            if let sample = samples?.first as? HKQuantitySample {
                let temp = sample.quantity.doubleValue(for: .degreeFahrenheit())
                completion(temp)
            } else {
                completion(nil)
            }
        }
        healthStore.execute(query)
    }

    func findFanAccessory() {
        // Locate fan accessory from HomeKit
        homeManager.delegate = self
    }

    func turnOnFan() {
        // Turn on the fan using HomeKit commands
        fanAccessory?.services.first?.characteristics.first?.writeValue(1, completionHandler: { error in
            if error == nil {
                print("Fan turned on!")
            }
        })
    }

    func turnOffFan() {
        // Turn off the fan
        fanAccessory?.services.first?.characteristics.first?.writeValue(0, completionHandler: { error in
            if error == nil {
                print("Fan turned off!")
            }
        })
    }
}

extension HeatStrokeMonitor: HMHomeManagerDelegate {
    func homeManagerDidUpdateHomes(_ manager: HMHomeManager) {
        // Find and store the fan accessory
        if let home = manager.primaryHome {
            fanAccessory = home.accessories.first { $0.name == "Fan" }
        }
    }
}
