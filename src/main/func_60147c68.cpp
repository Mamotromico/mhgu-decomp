extern "C" char* func_60147c68(char* base, unsigned int index)
{
    char* p = base + index * 0x44 + 0x18c;
    if (index < 0x18)
        return p + 0x3f400;
    return 0;
}