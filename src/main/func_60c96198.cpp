struct Unk60c96198 {
    char pad0[0x64];
    int field_0x64;
    char pad1[0x74 - 0x68];
    int field_0x74;
    int field_0x78;
    char pad2[0x80 - 0x7c];
    int field_0x80;
};

extern "C" int func_60c96198(Unk60c96198 *p)
{
    int idx = p->field_0x64;
    if (idx == 0)
        return 0xa;
    idx -= 1;
    p->field_0x64 = idx;
    char *base = (char *)p + (idx << 4);
    int v4 = *(int *)(base + 0x4);
    p->field_0x74 = v4;
    int v8 = *(int *)(base + 0x8);
    p->field_0x78 = v8;
    int vc = *(int *)(base + 0xc);
    p->field_0x80 = p->field_0x80 - vc;
    return 0;
}