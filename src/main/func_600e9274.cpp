extern "C" void func_600e9274(unsigned char *base, unsigned int index, unsigned char value)
{
    if (index <= 0xfU) {
        base[index + 0x254U] = value;
    }
}