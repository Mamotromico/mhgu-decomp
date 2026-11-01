extern "C" int func_60bf1c00(unsigned char* base, unsigned int index)
{
    unsigned int count = *(unsigned int*)(base + 0x31874);
    int result = 0;
    if (count > index) {
        unsigned char* p = base + index * 0xAB0;
        result = *(int*)(p + 0x2B844);
    }
    return result;
}