extern "C" int func_600bc7c4(void* base, unsigned int index)
{
    unsigned char* p = *reinterpret_cast<unsigned char**>(
        reinterpret_cast<unsigned char*>(base) + 0x1428);
    unsigned char* q = p + index * 4;
    return *reinterpret_cast<int*>(q + 0x254);
}