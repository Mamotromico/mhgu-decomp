extern "C" void func_603bfeec(char *base, unsigned int idx, char val)
{
    if (idx > 3)
        return;
    if ((unsigned char)base[0xaf19] != 1)
        return;
    base[idx + 0xd78a] = val;
}