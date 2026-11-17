extern "C" int func_6051030c(const unsigned char *p)
{
    int count = 0;
    if (*(const unsigned int *)(p + 0x1f8) != 0 ||
        *(const unsigned int *)(p + 0x1fc) != 0 ||
        *(const unsigned int *)(p + 0x200) != 0)
        count = 1;

    if (*(const unsigned int *)(p + 0x20c) != 0 ||
        *(const unsigned int *)(p + 0x210) != 0 ||
        *(const unsigned int *)(p + 0x214) != 0)
        count++;

    if (*(const unsigned int *)(p + 0x220) != 0 ||
        *(const unsigned int *)(p + 0x224) != 0 ||
        *(const unsigned int *)(p + 0x228) != 0)
        count++;

    if (*(const unsigned int *)(p + 0x234) != 0 ||
        *(const unsigned int *)(p + 0x238) != 0 ||
        *(const unsigned int *)(p + 0x23c) != 0)
        count++;

    if (*(const unsigned int *)(p + 0x248) != 0 ||
        *(const unsigned int *)(p + 0x24c) != 0 ||
        *(const unsigned int *)(p + 0x250) != 0)
        count++;

    if (*(const unsigned int *)(p + 0x25c) != 0 ||
        *(const unsigned int *)(p + 0x260) != 0 ||
        *(const unsigned int *)(p + 0x264) != 0)
        count++;

    if (*(const unsigned int *)(p + 0x270) != 0 ||
        *(const unsigned int *)(p + 0x274) != 0 ||
        *(const unsigned int *)(p + 0x278) != 0)
        count++;

    if (*(const unsigned int *)(p + 0x284) != 0 ||
        *(const unsigned int *)(p + 0x288) != 0 ||
        *(const unsigned int *)(p + 0x28c) != 0)
        count++;

    if (*(const unsigned int *)(p + 0x298) != 0 ||
        *(const unsigned int *)(p + 0x29c) != 0 ||
        *(const unsigned int *)(p + 0x2a0) != 0)
        count++;

    if (*(const unsigned int *)(p + 0x2ac) != 0 ||
        *(const unsigned int *)(p + 0x2b0) != 0 ||
        *(const unsigned int *)(p + 0x2b4) != 0)
        count++;

    return count;
}