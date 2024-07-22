clc 
clear

file = fopen("C:\Users\luizv\Desktop\ola_0.bin",'rb');
data_raw = fread(file, 'uint8');
fclose(file);

signedData = typecast(binaryData, 'int8');

% Convert the signed integers to hexadecimal strings
hexData = arrayfun(@(x) dec2hex(x, 2), signedData, 'UniformOutput', false);

% Concatenate the hexadecimal strings
hexString = strjoin(hexData, '');
