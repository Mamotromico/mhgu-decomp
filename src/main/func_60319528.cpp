extern "C" {
typedef struct {
    unsigned char pad[0x56];
    unsigned char field_0x56;
} S60319528;

void func_60319528(S60319528 *p) {
    p->field_0x56 |= 0x10;
}
}