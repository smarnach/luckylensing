#include "ll.h"
#include <values.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

extern void
ll_init_magpattern_params(struct ll_magpattern_param_t *params,
                          const struct ll_lenses_t *lenses,
                          const struct ll_rect_t *region,
                          unsigned xpixels, unsigned ypixels)
{
    params->lenses = *lenses;
    params->region = *region;
    params->xpixels = xpixels;
    params->ypixels = ypixels;
    params->pixels_per_width = xpixels / region->width;
    params->pixels_per_height = ypixels / region->height;
}

extern void
ll_init_rayshooter(struct ll_rayshooter_t *rs,
                   struct ll_magpattern_param_t *params, unsigned levels)
{
    rs->params = params;
    rs->levels = levels;
    rs->refine = 15;
    rs->refine_final = 25;
    rs->cancel = false;
}

extern void
ll_cancel_rayshooter(struct ll_rayshooter_t *rs)
{
    rs->cancel = true;
}

extern bool __attribute__ ((hot))
ll_shoot_single_ray(const struct ll_magpattern_param_t *params,
                    double x, double y, double *mag_x, double *mag_y)
{
    struct ll_lens_t *lens = params->lenses.lens;
    double x_deflected = x, y_deflected = y;
    for(unsigned i = 0; i < params->lenses.num_lenses; ++i)
    {
        double dx = x - lens[i].x;
        double dy = y - lens[i].y;
        double theta_squared = dx*dx + dy*dy;
        double deflection = lens[i].mass / theta_squared;
        x_deflected -= dx * deflection;
        y_deflected -= dy * deflection;
    }
    *mag_x = (x_deflected - params->region.x) * params->pixels_per_width;
    *mag_y = (y_deflected - params->region.y) * params->pixels_per_height;
    return (0 <= *mag_x && *mag_x < params->xpixels &&
            0 <= *mag_y && *mag_y < params->ypixels);
}

extern void
ll_rayshoot_rect(const struct ll_magpattern_param_t *params, float *magpat,
                 const struct ll_rect_t *rect, int xrays, int yrays)
{
    double width_per_xrays = rect->width / xrays;
    double height_per_yrays = rect->height / yrays;
    double mag_x, mag_y;
    for (int j = 0; j < yrays; ++j)
        for (int i = 0; i < xrays; ++i)
            if (ll_shoot_single_ray(params,
                                    rect->x + i*width_per_xrays,
                                    rect->y + j*height_per_yrays,
                                    &mag_x, &mag_y))
                ++magpat[(int)mag_y*params->xpixels + (int)mag_x];
}

static void __attribute__ ((hot))
_ll_rayshoot_bilinear(const struct ll_magpattern_param_t *params, float *magpat,
                      const struct ll_rect_t *rect, int refine)
{
    double ul_x, ul_y, ur_x, ur_y, ll_x, ll_y, lr_x, lr_y;
    double x0 = rect->x;
    double y0 = rect->y;
    double x1 = rect->x + rect->width;
    double y1 = rect->y + rect->height;
    bool ul = ll_shoot_single_ray(params, x0, y0, &ul_x, &ul_y);
    bool ur = ll_shoot_single_ray(params, x1, y0, &ur_x, &ur_y);
    bool ll = ll_shoot_single_ray(params, x0, y1, &ll_x, &ll_y);
    bool lr = ll_shoot_single_ray(params, x1, y1, &lr_x, &lr_y);
    double inv_refine = 1.0/refine;
    double ldown_x = (ll_x - ul_x) * inv_refine;
    double ldown_y = (ll_y - ul_y) * inv_refine;
    double rdown_x = (lr_x - ur_x) * inv_refine;
    double rdown_y = (lr_y - ur_y) * inv_refine;
    double right_x = (ur_x - ul_x) * inv_refine;
    double right_y = (ur_y - ul_y) * inv_refine;
    double update_x = (rdown_x - ldown_x) * inv_refine;
    double update_y = (rdown_y - ldown_y) * inv_refine;
    double sx = ul_x;
    double sy = ul_y;
    if (ul && ur && ll && lr)
        for (int j = 0; j < refine; ++j)
        {
            double x = sx;
            double y = sy;
            for (int i = 0; i < refine; ++i)
            {
                ++magpat[(int)y*params->xpixels + (int)x];
                x += right_x;
                y += right_y;
            }
            sx += ldown_x;
            sy += ldown_y;
            right_x += update_x;
            right_y += update_y;
        }
    else
        for (int j = 0; j < refine; ++j)
        {
            double x = sx;
            double y = sy;
            int i = 0;
            while ((x < 0.0 || x >= params->xpixels ||
                    y < 0.0 || y >= params->ypixels) &&
                   i < refine)
            {
                x += right_x;
                y += right_y;
                ++i;
            }
            while (i < refine &&
                   x >= 0.0 && x < params->xpixels &&
                   y >= 0.0 && y < params->ypixels)
            {
                ++magpat[(int)y*params->xpixels + (int)x];
                x += right_x;
                y += right_y;
                ++i;
            }
            sx += ldown_x;
            sy += ldown_y;
            right_x += update_x;
            right_y += update_y;
        }
}

static void __attribute__ ((hot))
_ll_rayshoot_triangulated(const struct ll_magpattern_param_t *params, float *magpat,
                          const struct ll_rect_t *rect)
{
    double tri_vertices[3][2];
    double x0 = rect->x;
    double y0 = rect->y;
    double x1 = rect->x + rect->width;
    double y1 = rect->y + rect->height;
    ll_shoot_single_ray(params, x0, y0, tri_vertices[0], tri_vertices[0]+1);
    ll_shoot_single_ray(params, x0, y1, tri_vertices[1], tri_vertices[1]+1);
    ll_shoot_single_ray(params, x1, y0, tri_vertices[2], tri_vertices[2]+1);

    for (int triangle = 0; triangle < 2; ++triangle)
    {
        if (triangle == 1)
        {
            tri_vertices[0][0] = tri_vertices[2][0];
            tri_vertices[0][1] = tri_vertices[2][1];
            ll_shoot_single_ray(params, x1, y1, tri_vertices[2], tri_vertices[2]+1);
        }

        // Get minimum and maximum x coordinate in the magpattern
        bool single_pixel_optimization = true;
        int min = 0, max = 0;
        if (tri_vertices[1][0] < tri_vertices[0][0])
            min = 1;
        else
            max = 1;
        if (tri_vertices[2][0] < tri_vertices[min][0])
            min = 2;
        if (tri_vertices[2][0] > tri_vertices[max][0])
            max = 2;
        int mag_x0 = tri_vertices[min][0];
        if (mag_x0 >= (int)params->xpixels)
            continue;
        if (mag_x0 < 0)
        {
            mag_x0 = 0;
            single_pixel_optimization = false;
        }
        if (tri_vertices[max][0] < 0.0)
            continue;
        int mag_x1 = tri_vertices[max][0];
        if (mag_x1 >= (int)params->xpixels)
        {
            mag_x1 = params->xpixels - 1;
            single_pixel_optimization = false;
        }

        // Get minimum and maximum y coordinate in the magpattern
        min = 0, max = 0;
        if (tri_vertices[1][1] < tri_vertices[0][1])
            min = 1;
        else
            max = 1;
        if (tri_vertices[2][1] < tri_vertices[min][1])
            min = 2;
        if (tri_vertices[2][1] > tri_vertices[max][1])
            max = 2;
        int mag_y0 = tri_vertices[min][1];
        if (mag_y0 >= (int)params->ypixels)
            continue;
        if (mag_y0 < 0)
        {
            mag_y0 = 0;
            single_pixel_optimization = false;
        }
        if (tri_vertices[max][1] < 0.0)
            continue;
        int mag_y1 = tri_vertices[max][1];
        if (mag_y1 >= (int)params->ypixels)
        {
            mag_y1 = params->ypixels - 1;
            single_pixel_optimization = false;
        }

        double tri_area =
            (tri_vertices[1][0]-tri_vertices[0][0]) *
            (tri_vertices[2][1]-tri_vertices[0][1]) -
            (tri_vertices[1][1]-tri_vertices[0][1]) *
            (tri_vertices[2][0]-tri_vertices[0][0]);
        if (tri_area < 0.0)
        {
            tri_area *= -1.0;
            double x = tri_vertices[1][0];
            double y = tri_vertices[1][1];
            tri_vertices[1][0] = tri_vertices[2][0];
            tri_vertices[1][1] = tri_vertices[2][1];
            tri_vertices[2][0] = x;
            tri_vertices[2][1] = y;
        }

        // Render the triangle
        if (single_pixel_optimization && mag_x0 == mag_x1 && mag_y0 == mag_y1)
        {
            // The triangle is completely contained in a single pixel,
            // so we can take a shortcut
            magpat[mag_y0*params->xpixels + mag_x0] += 1.0;
            continue;
        }
        for (int y = mag_y0; y <= mag_y1; ++y)
        {
            double yi0 = y;
            double yi1 = y + 1;

            for (int x = mag_x0; x <= mag_x1; ++x)
            {
                double xi0 = x;
                double xi1 = x + 1;

                int num_edges = 4;
                bool valid_edges[7] =
                    {true, true, true, true, false, false, false};
                bool valid_vertices[7] =
                    {true, true, true, true, false, false, false};
                struct Line {
                    double normal[2];
                    double dist;
                } edges[7];
                edges[0].normal[0] = -1.0; edges[0].normal[1] =  0.0; edges[0].dist = xi0;
                edges[1].normal[0] =  1.0; edges[1].normal[1] =  0.0; edges[1].dist = -xi1;
                edges[2].normal[0] =  0.0; edges[2].normal[1] = -1.0; edges[2].dist = yi0;
                edges[3].normal[0] =  0.0; edges[3].normal[1] =  1.0; edges[3].dist = -yi1;
                double vertices[7][2];
                vertices[0][0] = xi0; vertices[0][1] = yi0;
                vertices[1][0] = xi1; vertices[1][1] = yi0;
                vertices[2][0] = xi0; vertices[2][1] = yi1;
                vertices[3][0] = xi1; vertices[3][1] = yi1;
                int vertex_indices[7][2];
                vertex_indices[0][0] = 2; vertex_indices[0][1] = 0;
                vertex_indices[1][0] = 1; vertex_indices[1][1] = 3;
                vertex_indices[2][0] = 0; vertex_indices[2][1] = 1;
                vertex_indices[3][0] = 3; vertex_indices[3][1] = 2;

                int k = 0;
                for (int lastk = 2; k < 3; lastk = k, ++k)
                {
                    struct Line l;
                    l.normal[0] = tri_vertices[k][1] - tri_vertices[lastk][1];
                    l.normal[1] = tri_vertices[lastk][0] - tri_vertices[k][0];
                    l.dist = (-l.normal[0] * tri_vertices[k][0]
                              -l.normal[1] * tri_vertices[k][1]);

                    double vertex_values[7];
                    int min_invalid_vertex = 7;
                    int min_invalid_edge = 7;
                    for(int i = 0; i < 7; ++i)
                    {
                        if (valid_vertices[i])
                            vertex_values[i] = l.normal[0]*vertices[i][0] +
                                l.normal[1]*vertices[i][1] + l.dist;
                        else
                            if (i < min_invalid_vertex)
                                min_invalid_vertex = i;
                        if (!valid_edges[i] && i < min_invalid_edge)
                            min_invalid_edge = i;
                    }

                    int num_cuts = 0;
                    double new_vertex[2][2];
                    for(int i = 0; i < 7; ++i)
                    {
                        if (!valid_edges[i])
                            continue;
                        int v0 = vertex_indices[i][0];
                        int v1 = vertex_indices[i][1];
                        double a0 = vertex_values[v0];
                        double a1 = vertex_values[v1];
                        if (a0 < 0.0)
                        {
                            if (a1 >= 0.0)
                            {
                                double t = a0/(a0-a1);
                                new_vertex[0][0] = vertices[v0][0] +
                                    t*(vertices[v1][0] - vertices[v0][0]);
                                new_vertex[0][1] = vertices[v0][1] +
                                    t*(vertices[v1][1] - vertices[v0][1]);
                                vertex_indices[min_invalid_edge][0] = v1;
                                ++num_cuts;
                            }
                        } else {
                            if (a1 < 0.0)
                            {
                                double t = a0/(a0-a1);
                                new_vertex[1][0] = vertices[v0][0] +
                                    t*(vertices[v1][0] - vertices[v0][0]);
                                new_vertex[1][1] = vertices[v0][1] +
                                    t*(vertices[v1][1] - vertices[v0][1]);
                                vertex_indices[i][0] = min_invalid_vertex;
                                vertex_indices[min_invalid_edge][1] = min_invalid_vertex;
                                valid_vertices[min_invalid_vertex] = true;
                                ++num_cuts;
                            } else {
                                valid_edges[i] = false;
                                --num_edges;
                                valid_vertices[v1] = false;
                                if (num_edges <= 1)
                                    break;
                            }
                        }
                    }
                    if (num_edges <= 1)
                        break;
                    if (num_cuts)
                    {
                        struct Line *new_l = edges + min_invalid_edge;
                        new_l->normal[0] = l.normal[0];
                        new_l->normal[1] = l.normal[1];
                        new_l->dist = l.dist;
                        vertices[vertex_indices[min_invalid_edge][0]][0] = new_vertex[0][0];
                        vertices[vertex_indices[min_invalid_edge][0]][1] = new_vertex[0][1];
                        vertices[vertex_indices[min_invalid_edge][1]][0] = new_vertex[1][0];
                        vertices[vertex_indices[min_invalid_edge][1]][1] = new_vertex[1][1];
                        valid_edges[min_invalid_edge] = true;
                        ++num_edges;
                    }
                }
                if (k == 3)
                {
                    double area = 0.0;
                    int j = 0;
                    while (!valid_vertices[j])
                        ++j;
                    double x0 = vertices[j][0];
                    double y0 = vertices[j][1];
                    for(int i = 0; i < 7; ++i)
                        if (valid_edges[i])
                        {
                            int i0 = vertex_indices[i][0];
                            int i1 = vertex_indices[i][1];
                            area +=  (vertices[i0][0]-x0) * (vertices[i1][1]-y0)
                                - (vertices[i0][1]-y0) * (vertices[i1][0]-x0);
                        }
                    magpat[y*params->xpixels + x] += fabs(area) / tri_area;
                }
            }
        }
    }
}

static void
_ll_rayshoot_recursively(const struct ll_rayshooter_t *rs, float *magpat,
                         const struct ll_rect_t *rect, int xrays, int yrays,
                         unsigned level, double *progress)
{
    if (rs->cancel)
        return;
    if (level)
    {
        struct ll_patches_t patches =
            { *rect, xrays, yrays, rect->width/xrays, rect->height/yrays,
              .hit = malloc(xrays*yrays * sizeof(char)), .num_patches = 0};
        ll_get_subpatches(rs->params, &patches);
        ll_rayshoot_subpatches(rs, magpat, &patches, level, progress);
        free(patches.hit);
    }
    else
//        _ll_rayshoot_bilinear(rs->params, magpat, rect, rs->refine_final);
        _ll_rayshoot_triangulated(rs->params, magpat, rect);
}

extern void
ll_get_subpatches(const struct ll_magpattern_param_t *params,
                  struct ll_patches_t *patches)
{
    int xrays = patches->xrays;
    int yrays = patches->yrays;
    double xpixels = params->xpixels;
    double ypixels = params->ypixels;
    int *hit = malloc((xrays+3)*(yrays+3) * sizeof(int));
    for (int j = -1, m = 0; j <= yrays+1; ++j)
        for (int i = -1; i <= xrays+1; ++i, ++m)
        {
            double mag_x, mag_y;
            ll_shoot_single_ray(params,
                                patches->rect.x + i*patches->width_per_xrays,
                                patches->rect.y + j*patches->height_per_yrays,
                                &mag_x, &mag_y);
            hit[m] = (((0 <= mag_x)     ) | ((mag_x < xpixels) << 1) |
                      ((0 <= mag_y) << 2) | ((mag_y < ypixels) << 3));
        }
    patches->num_patches = 0;
    char* hit_patches = patches->hit;
    for (int j = 0, m = xrays+4, n = 0; j < yrays; ++j, m += 3)
        for (int i = 0; i < xrays; ++i, ++m, ++n)
        {
            hit_patches[n] = (hit[m-xrays-3] | hit[m-xrays-2] |
                              hit[m-1] | hit[m] | hit[m+1] | hit[m+2] |
                              hit[m+xrays+2] | hit[m+xrays+3] |
                              hit[m+xrays+4] | hit[m+xrays+5] |
                              hit[m+2*xrays+6] | hit[m+2*xrays+7]) == 15;
            if (hit_patches[n])
                ++patches->num_patches;
        }
    free(hit);
}

extern void
ll_rayshoot_subpatches(const struct ll_rayshooter_t *rs, float *magpat,
                       const struct ll_patches_t *patches,
                       unsigned level, double *progress)
{
    double progress_inc = 1.0 / patches->num_patches;
    for (int j = 0, n = 0; j < patches->yrays; ++j)
        for (int i = 0; i < patches->xrays; ++i, ++n)
            if (patches->hit[n])
            {
                double x = patches->rect.x + i*patches->width_per_xrays;
                double y = patches->rect.y + j*patches->height_per_yrays;
                struct ll_rect_t subrect
                    = {x, y, patches->width_per_xrays, patches->height_per_yrays};
                _ll_rayshoot_recursively(rs, magpat, &subrect, rs->refine,
                                         rs->refine, level-1, 0);
                if (progress)
                    *progress += progress_inc;
            }
}

extern void
ll_rayshoot(const struct ll_rayshooter_t *rs, float *magpat,
            const struct ll_rect_t *rect, int xrays, int yrays,
            double *progress)
{
    if (progress)
        *progress = 0.0;
    _ll_rayshoot_recursively(rs, magpat, rect, xrays, yrays,
                             rs->levels - 1, progress);
}

extern void
ll_ray_hit_pattern(const struct ll_magpattern_param_t *params, char *buf,
                   const struct ll_rect_t *rect)
{
    double width_per_xrays = rect->width / params->xpixels;
    double height_per_yrays = rect->height / params->ypixels;
    double mag_x, mag_y;
    for (unsigned j = 0; j < params->ypixels; ++j)
        for (unsigned i = 0; i < params->xpixels; ++i)
            buf[j*params->xpixels + i] = 255 *
                ll_shoot_single_ray(params,
                                    rect->x + i*width_per_xrays,
                                    rect->y + j*height_per_yrays,
                                    &mag_x, &mag_y);
}

extern void
ll_source_images(const struct ll_magpattern_param_t *params, char *buf,
                 const struct ll_rect_t *rect, int xrays, int yrays,
                 int refine, double source_x, double source_y, double source_r)
{
    double r_squared = source_r*source_r;
    double width_per_xrays = rect->width / xrays;
    double height_per_yrays = rect->height / yrays;
    double x_inc = width_per_xrays / refine;
    double y_inc = height_per_yrays / refine;
    int buf_inc = 255 / (refine*refine);
    for (int j = 0, m = 0; j < xrays; ++j)
        for (int i = 0; i < yrays; ++i, ++m)
        {
            double x0 = rect->x + i*width_per_xrays;
            double y = rect->y + j*height_per_yrays;
            for (int k = 0; k < refine; ++k)
            {
                double x = x0;
                for (int l = 0; l < refine; ++l)
                {
                    double mag_x, mag_y;
                    ll_shoot_single_ray(params, x, y, &mag_x, &mag_y);
                    double dx = source_x - mag_x;
                    double dy = source_y - mag_y;
                    if (dx*dx + dy*dy < r_squared)
                        buf[m] += buf_inc;
                    x += x_inc;
                }
                y += y_inc;
            }
        }
}

extern void
ll_render_magpattern_greyscale(char *buf, const float *magpat, unsigned size)
{
    float max_count = 0.0;
    float min_count = __FLT_MAX__;
    for(unsigned i = 0; i < size; ++i)
    {
        if (magpat[i] > max_count)
            max_count = magpat[i];
        if (magpat[i] < min_count)
            min_count = magpat[i];
    }
    if (max_count == min_count)
        return;
    double logmax = log(max_count+1e-10);
    double logmin = log(min_count+1e-10);
    double factor = 255/(logmax-logmin);
    for(unsigned i = 0; i < size; ++i)
        buf[i] = (log(magpat[i]+1e-10)-logmin)*factor;
}

extern void
ll_light_curve(const struct ll_magpattern_param_t *params, const float *magpat,
               double *curve, unsigned num_points,
               double x0, double y0, double x1, double y1)
{
    double mag_x = (x0 - params->region.x) * params->pixels_per_width;
    double mag_y = (y0 - params->region.y) * params->pixels_per_height;
    double dx = (x1 - x0) * params->pixels_per_width / (num_points - 1);
    double dy = (y1 - y0) * params->pixels_per_height / (num_points - 1);
    for (unsigned i = 0; i < num_points; ++i)
    {
        int ix = mag_x;
        int iy = mag_y;
        int index = iy*params->xpixels + ix;
        double frac_x = mag_x - ix;
        double frac_y = mag_y - iy;
        curve[i] = (1.0 - frac_x) * (1.0 - frac_y) * magpat[index]
            + frac_x * (1.0 - frac_y) * magpat[index+1]
            + (1.0 - frac_x) * frac_y * magpat[index+params->xpixels]
            + frac_x * frac_y * magpat[index+params->xpixels+1];
        mag_x += dx;
        mag_y += dy;
    }
}
