#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    unsigned char _pad[0xba];
    unsigned char flags;
} struct_func_603ae768;

int func_603ae768(const struct_func_603ae768 *s)
{
    return (s->flags >> 3) & 1;
}

#ifdef __cplusplus
}
#endif