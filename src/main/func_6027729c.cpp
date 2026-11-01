extern "C" int func_6027729c(char *base, int index)
{
    int *entry = (int *)(base + index * 4);
    int obj = entry[7];
    if (obj == 0)
        return 0;
    int val = *(int *)(obj + 0x13c8);
    if (val != 1)
        return 0;
    return obj;
}