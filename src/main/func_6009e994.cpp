extern "C" unsigned int func_6009e994(unsigned char *p)
{
    unsigned char *q = *reinterpret_cast<unsigned char **>(p + 0x1428);
    return (static_cast<unsigned int>(q[0x5ccb]) >> 3) & 7u;
}