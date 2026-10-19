extern "C" void func_600e9ea4(char *base, unsigned int index, char value)
{
    if (index <= 0xb) {
        base[index + 0x264] = value;
    }
}