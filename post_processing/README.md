# Calculate Flux

1. First get ChipIR files (countlogs in .txt format)
2. Get Facility factor
3. Get distance file. 
4. Define time window
5. Execute the scripts and calculate average flux for time window
   
## ChipIR Files and Facility Factor

Need to be retrieved from the facility before we leave. Carlo needs to help with this.

Facility Factor is a variable retrieved from the beam calibration, Carlo needs to provide it.

## Distance File
Distance file is an excel we create at the facility, containing the distances of each device to the beam line. We then use the facility_factor and distances to calculate the distance attenuation.

Start and end are not really required, but serve as an additional filter if you changed boards often.

```csv
board | distance | start | end | facility_factor | Distance attenuation
```

## Time window

Defining a time window is a difficult task for our current experiments. The way Fernando does is to set all of the experiments with a minimal 1 hour of duration. Then he calculates the average flux for those 1 hour windows.

Using smaller windows has diminishing gains, as you gain marginally on accuracy, but calculating the final cross-section becomes harder.

## Scripts

As they are today, the scripts take 2 argumnets:

```bash
python calculate_flux.py <neutron counts input file> <distance facility_factor file>
```

neutron counts input file -- agregate data from all of the countlogs
distance facility_factor file -- the csv described before
