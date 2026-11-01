extern "C" unsigned func_60524d68(const unsigned char* base, unsigned bit)
{
    unsigned wordIndex = bit >> 5;
    unsigned bitIndex = bit & 0x1f;
    unsigned word = *reinterpret_cast<const unsigned*>(base + 0x3598 + wordIndex * 4);
    unsigned mask = 1u << bitIndex;
    return (word & mask) ? 1u : 0u;
}