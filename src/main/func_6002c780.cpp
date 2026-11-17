extern "C" void func_6002c780(char *p)
{
    unsigned v = *(unsigned *)(p + 0x1c) - 1;
    if (v > 0x270e) {
        *(unsigned *)(p + 0x2c) = 0;
        *(unsigned *)(p + 0x30) = 9;
        *(unsigned *)(p + 0x34) = 9;
        *(unsigned *)(p + 0x24) = 0;
        *(unsigned *)(p + 0x1c) = 1000;
    }
}