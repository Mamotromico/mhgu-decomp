typedef struct {
    unsigned char pad[0x2506];
    unsigned short field;
} S;

extern "C" int func_602a67f4(S *s)
{
    return s->field == 0x100;
}