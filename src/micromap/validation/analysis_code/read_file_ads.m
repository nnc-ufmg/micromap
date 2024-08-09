clc 
clear

% Open the binary file (adjust the path as necessary)
file = fopen("C:\Users\luizv\Desktop\UFMG\NNC\micromap\src\micromap\interface\records\tests\test_potentiometer",'r');

% Read the raw data as unsigned 8-bit integers
data_raw = fread(file, 'uint8=>uint8');
fclose(file);

% Constants
num_channels = 8;     % Number of channels
bytes_per_sample = 27; % 3 bytes for status word + 3 bytes per channel * 8 channels

% Ensure data length is a multiple of bytes_per_sample
total_bytes = length(data_raw);
num_samples = floor(total_bytes / bytes_per_sample);

% Trim any excess bytes
data_raw = data_raw(1:(num_samples * bytes_per_sample));

% Reshape data into samples
data_raw = reshape(data_raw, bytes_per_sample, num_samples);

% Extract channel data
data = zeros(num_channels, num_samples);

for i = 1:num_channels
    % Extract 3 bytes per channel per sample
    channel_data = data_raw(4 + (i-1)*3 : 6 + (i-1)*3, :);
    
    % Convert from 3 bytes (24-bit) to signed integers
    channel_data_int = typecast(reshape(uint8(channel_data), [], 1), 'int32');
    
    % Shift right by 8 bits to match the 24-bit data alignment
    data(i, :) = double(bitshift(channel_data_int, -8));
end

% Apply scaling factor (as per your previous code)
scaling_factor = 7.9473e-8; % From your Python code
data = data * scaling_factor;

% Plot the data
figure(1)
for a = 1:num_channels
    subplot(4, 2, a)
    plot(data(a, :))
    title(['Channel ', num2str(a)])
    % ylim([-1000, 1000]) % Uncomment and adjust if you want to limit the y-axis
end
hold on
