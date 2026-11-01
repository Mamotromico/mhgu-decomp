extern "C" unsigned func_607cbdb4(const unsigned char *s, unsigned crc)
{
    unsigned char c = s[0];
    if (c != 0) {
        s++;
        do {
            crc = __builtin_arm_crc32b(crc, c);
            c = *s++;
        } while (c != 0);
    }
    return crc;
}