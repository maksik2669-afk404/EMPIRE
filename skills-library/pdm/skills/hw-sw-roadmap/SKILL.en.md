---
name: hw-sw-roadmap
description: Develop a roadmap for synchronizing hardware and software (Hardware + Software / IoT Roadmap).
argument-hint: [description of the physical device/gadget and software for synchronizing roadmaps]
allowed-tools: Read, Write
preset: platforms-tech
lifecycle: any
business-model: any
domain: generic
stage: any
output-artifact: document
---

# Synchronization of HW and SW (hw-sw-roadmap)

Develop an integrated roadmap for IoT products or electronics, coordinating the development cycles of the physical device (Hardware) and firmware/mobile application (Software).

## Process
1. **Define hardware constraints (HW Constraints).** Order components, PCB production, device certification.
2. **Synchronize development phases.** EVT (engineering test), DVT (design test), PVT (pre-production release) with firmware and mobile application releases.
3. **Describe the dependencies.** Which software features require specific sensors in the hardware.
4. **Save the output** in the current working directory as `hw-sw-roadmap-[context].md`.

## Output Format
```
## Integrated IoT Roadmap: [Device Name]
- **Hardware Phase (HW):** DVT testing of boards (completion by [Date]).
- **Software dependency:** The release of the Bluetooth authorization function in the application is tied to the completion of firmware v1.2.
```


## Rules

- Write in English.
## Metrics

### Universal Metric Rule
If you propose a metric, answer these 5 questions:
1. **Who owns this metric?**
2. **How often do we track it?**
3. **What events calculate it?**
4. **What is the decision threshold?**
5. **How can it be gamed or corrupted?