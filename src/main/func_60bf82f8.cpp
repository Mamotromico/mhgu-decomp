extern "C" void func_60bf82f8(char* out, char** in)
{
    char* src = *in;
    *(unsigned int*)(out + 0x0) = *(unsigned int*)(src + 0x40);
    *(unsigned int*)(out + 0x4) = *(unsigned int*)(src + 0x44);
    *(unsigned int*)(out + 0x8) = *(unsigned int*)(src + 0x48);
    *(unsigned int*)(out + 0xc) = 0;
}