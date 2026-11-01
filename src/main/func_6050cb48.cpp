extern "C" void func_6050cb48(char* r0, const char* r1)
{
    *(unsigned int*)(r0 + 0x2d0) = *(const unsigned int*)(r1 + 0x0);
    *(unsigned int*)(r0 + 0x2d4) = *(const unsigned int*)(r1 + 0x4);
    *(unsigned int*)(r0 + 0x2d8) = *(const unsigned int*)(r1 + 0x8);
    *(unsigned int*)(r0 + 0x2dc) = 0;
    unsigned long long v = *(const unsigned long long*)(r1 + 0x10);
    *(unsigned long long*)(r0 + 0x2e0) = v;
}