extern "C" void func_60523b7c(unsigned short *base, int index)
{
    unsigned short *slot = base + index + 0x8d;
    unsigned short value = *slot;

    if (value <= 0xea5f) {
        value++;
        *slot = value;
    }
}