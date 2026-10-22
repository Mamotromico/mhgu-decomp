extern "C" void* func_6019e1e4(unsigned int* base, unsigned int index, const unsigned short* src)
{
    unsigned char* p = reinterpret_cast<unsigned char*>(base + index);
    unsigned short v0 = src[0];
    unsigned short v1 = src[1];
    *reinterpret_cast<unsigned short*>(p + 0x1c) = v1;
    *reinterpret_cast<unsigned short*>(p + 0x1a) = v0;
    return p;
}